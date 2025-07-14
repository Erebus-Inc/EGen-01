"""Trainer for the THL-150 model."""

import os
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import torch
import torch.distributed as dist
import torch.nn as nn
from torch.cuda.amp import GradScaler, autocast
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, Dataset, DistributedSampler

from egen.model import THL150
from egen.training.config import TrainingConfig
from egen.training.utils import (
    get_optimizer,
    get_scheduler,
    save_checkpoint,
    load_checkpoint,
    get_latest_checkpoint,
    set_seed,
)


class Trainer:
    """Trainer for the THL-150 model."""

    def __init__(
        self,
        model: THL150,
        train_dataset: Optional[Dataset] = None,
        eval_dataset: Optional[Dataset] = None,
        config: Optional[TrainingConfig] = None,
        tokenizer: Optional[Any] = None,
    ):
        """Initialize the trainer."""
        self.model = model
        self.train_dataset = train_dataset
        self.eval_dataset = eval_dataset
        self.config = config or TrainingConfig()
        self.tokenizer = tokenizer
        
        # Set seed for reproducibility
        set_seed(self.config.seed)
        
        # Setup device
        self.device = self._setup_device()
        
        # Move model to device
        self.model.to(self.device)
        
        # Setup distributed training if enabled
        if self.config.distributed_training:
            self._setup_distributed()
        
        # Setup mixed precision training if enabled
        self.scaler = GradScaler() if self.config.use_mixed_precision and self.config.fp16 else None
        
        # Setup optimizer and scheduler
        self.optimizer = None
        self.scheduler = None
        
        # Training state
        self.epoch = 0
        self.global_step = 0
        self.best_metric = float("inf")
        
        # Initialize training
        if self.train_dataset is not None:
            self._setup_training()
    
    def _setup_device(self) -> torch.device:
        """Setup device for training."""
        if self.config.no_cuda or not torch.cuda.is_available():
            return torch.device("cpu")
        
        return torch.device("cuda")
    
    def _setup_distributed(self) -> None:
        """Setup distributed training."""
        if self.config.local_rank == -1:
            return
        
        # Initialize process group
        if not dist.is_initialized():
            dist.init_process_group(backend=self.config.distributed_backend)
        
        # Set device
        torch.cuda.set_device(self.config.local_rank)
        self.device = torch.device("cuda", self.config.local_rank)
        
        # Wrap model with DDP
        self.model = DDP(
            self.model,
            device_ids=[self.config.local_rank],
            output_device=self.config.local_rank,
            find_unused_parameters=self.config.ddp_find_unused_parameters,
        )
    
    def _setup_training(self) -> None:
        """Setup training components."""
        # Create optimizer
        self.optimizer = get_optimizer(self.model, self.config)
        
        # Calculate number of training steps
        train_dataloader = self.get_train_dataloader()
        num_update_steps_per_epoch = len(train_dataloader) // self.config.gradient_accumulation_steps
        max_steps = self.config.num_train_epochs * num_update_steps_per_epoch
        
        # Create scheduler
        self.scheduler = get_scheduler(self.optimizer, max_steps, self.config)
        
        # Resume from checkpoint if specified
        if self.config.resume_from_checkpoint:
            self._resume_from_checkpoint()
    
    def _resume_from_checkpoint(self) -> None:
        """Resume training from checkpoint."""
        checkpoint_path = self.config.resume_from_checkpoint
        
        # If checkpoint path is a directory, find the latest checkpoint
        if os.path.isdir(checkpoint_path):
            checkpoint_path = get_latest_checkpoint(checkpoint_path)
        
        if checkpoint_path is None:
            return
        
        # Load checkpoint
        self.epoch, self.global_step, _, _ = load_checkpoint(
            checkpoint_path,
            self.model,
            self.optimizer if self.config.save_optimizer else None,
            self.scheduler if self.config.save_scheduler else None,
            self.device,
        )
    
    def get_train_dataloader(self) -> DataLoader:
        """Get training dataloader."""
        if self.train_dataset is None:
            raise ValueError("Trainer: training requires a train_dataset.")
        
        # Create sampler for distributed training
        train_sampler = None
        if self.config.distributed_training:
            train_sampler = DistributedSampler(
                self.train_dataset,
                num_replicas=dist.get_world_size(),
                rank=dist.get_rank(),
                shuffle=True,
            )
        
        # Create dataloader
        train_dataloader = DataLoader(
            self.train_dataset,
            batch_size=self.config.per_device_train_batch_size,
            sampler=train_sampler,
            shuffle=train_sampler is None,
            drop_last=self.config.dataloader_drop_last,
            num_workers=self.config.dataloader_num_workers,
            pin_memory=self.config.dataloader_pin_memory,
        )
        
        return train_dataloader
    
    def get_eval_dataloader(self) -> DataLoader:
        """Get evaluation dataloader."""
        if self.eval_dataset is None:
            raise ValueError("Trainer: evaluation requires an eval_dataset.")
        
        # Create dataloader
        eval_dataloader = DataLoader(
            self.eval_dataset,
            batch_size=self.config.per_device_eval_batch_size,
            shuffle=False,
            drop_last=self.config.dataloader_drop_last,
            num_workers=self.config.dataloader_num_workers,
            pin_memory=self.config.dataloader_pin_memory,
        )
        
        return eval_dataloader
    
    def train(self) -> Dict[str, float]:
        """Train the model."""
        if self.train_dataset is None:
            raise ValueError("Trainer: training requires a train_dataset.")
        
        # Get training dataloader
        train_dataloader = self.get_train_dataloader()
        
        # Enable gradient checkpointing if configured
        if self.config.gradient_checkpointing:
            self.model.gradient_checkpointing_enable()
        
        # Set model to training mode
        self.model.train()
        
        # Training loop
        total_train_loss = 0.0
        num_train_steps = 0
        start_time = time.time()
        
        for epoch in range(self.epoch, int(self.config.num_train_epochs)):
            self.epoch = epoch
            epoch_start_time = time.time()
            epoch_loss = 0.0
            epoch_steps = 0
            
            # Set epoch for distributed sampler
            if self.config.distributed_training and isinstance(train_dataloader.sampler, DistributedSampler):
                train_dataloader.sampler.set_epoch(epoch)
            
            # Batch loop
            for step, batch in enumerate(train_dataloader):
                # Move batch to device
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                # Forward pass with mixed precision if enabled
                if self.config.use_mixed_precision and self.config.fp16:
                    with autocast():
                        outputs = self.model(**batch)
                        loss = outputs["loss"] if isinstance(outputs, dict) else outputs[0]
                        loss = loss / self.config.gradient_accumulation_steps
                    
                    # Backward pass with gradient scaling
                    self.scaler.scale(loss).backward()
                else:
                    # Standard forward and backward pass
                    outputs = self.model(**batch)
                    loss = outputs["loss"] if isinstance(outputs, dict) else outputs[0]
                    loss = loss / self.config.gradient_accumulation_steps
                    loss.backward()
                
                # Update weights if gradient accumulation steps reached
                if (step + 1) % self.config.gradient_accumulation_steps == 0:
                    if self.config.use_mixed_precision and self.config.fp16:
                        # Unscale gradients and clip
                        self.scaler.unscale_(self.optimizer)
                        torch.nn.utils.clip_grad_norm_(
                            self.model.parameters(), self.config.max_grad_norm
                        )
                        
                        # Update weights with gradient scaling
                        self.scaler.step(self.optimizer)
                        self.scaler.update()
                    else:
                        # Standard gradient clipping and update
                        torch.nn.utils.clip_grad_norm_(
                            self.model.parameters(), self.config.max_grad_norm
                        )
                        self.optimizer.step()
                    
                    # Update learning rate
                    self.scheduler.step()
                    
                    # Zero gradients
                    self.optimizer.zero_grad()
                    
                    # Update global step
                    self.global_step += 1
                
                # Update loss tracking
                epoch_loss += loss.item() * self.config.gradient_accumulation_steps
                epoch_steps += 1
                
                # Evaluation
                if self.config.do_eval and self.global_step % self.config.eval_steps == 0:
                    eval_results = self.evaluate()
                    self.model.train()  # Set model back to training mode
                    
                    # Save checkpoint if best model
                    if self.config.load_best_model_at_end:
                        metric_to_check = self.config.metric_for_best_model or "loss"
                        metric_value = eval_results.get(metric_to_check)
                        
                        if metric_value is not None:
                            is_better = False
                            if self.config.greater_is_better:
                                is_better = metric_value > self.best_metric
                            else:
                                is_better = metric_value < self.best_metric
                            
                            if is_better:
                                self.best_metric = metric_value
                                self._save_checkpoint("best_model")
                
                # Save checkpoint
                if self.config.save_strategy == "steps" and self.global_step % self.config.save_steps == 0:
                    self._save_checkpoint()
            
            # End of epoch
            epoch_loss /= epoch_steps
            epoch_time = time.time() - epoch_start_time
            total_train_loss += epoch_loss
            num_train_steps += epoch_steps
            
            print(f"Epoch {epoch+1}/{int(self.config.num_train_epochs)} - "
                  f"Loss: {epoch_loss:.4f} - Time: {epoch_time:.2f}s")
            
            # Save checkpoint at end of epoch
            if self.config.save_strategy == "epoch":
                self._save_checkpoint()
        
        # End of training
        total_train_loss /= num_train_steps
        total_time = time.time() - start_time
        
        print(f"Training complete - "
              f"Loss: {total_train_loss:.4f} - Time: {total_time:.2f}s")
        
        # Final evaluation
        eval_results = {}
        if self.config.do_eval:
            eval_results = self.evaluate()
        
        # Save final model
        self._save_checkpoint("final")
        
        # Return training metrics
        train_metrics = {"train_loss": total_train_loss, "train_time": total_time}
        train_metrics.update(eval_results)
        
        return train_metrics
    
    def evaluate(self) -> Dict[str, float]:
        """Evaluate the model."""
        if self.eval_dataset is None:
            raise ValueError("Trainer: evaluation requires an eval_dataset.")
        
        # Get evaluation dataloader
        eval_dataloader = self.get_eval_dataloader()
        
        # Set model to evaluation mode
        self.model.eval()
        
        # Evaluation loop
        eval_loss = 0.0
        num_eval_steps = 0
        start_time = time.time()
        
        # Disable gradient computation
        with torch.no_grad():
            for batch in eval_dataloader:
                # Move batch to device
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                # Forward pass
                outputs = self.model(**batch)
                loss = outputs["loss"] if isinstance(outputs, dict) else outputs[0]
                
                # Update loss tracking
                eval_loss += loss.item()
                num_eval_steps += 1
        
        # Calculate metrics
        eval_loss /= num_eval_steps
        eval_time = time.time() - start_time
        
        # Calculate perplexity if loss is cross-entropy
        perplexity = torch.exp(torch.tensor(eval_loss)).item()
        
        print(f"Evaluation - Loss: {eval_loss:.4f} - "
              f"Perplexity: {perplexity:.2f} - Time: {eval_time:.2f}s")
        
        # Return evaluation metrics
        eval_metrics = {
            "eval_loss": eval_loss,
            "eval_perplexity": perplexity,
            "eval_time": eval_time,
        }
        
        return eval_metrics
    
    def _save_checkpoint(self, checkpoint_name: str = "checkpoint") -> None:
        """Save model checkpoint."""
        # Skip saving on non-master process in distributed training
        if self.config.distributed_training and dist.get_rank() != 0:
            return
        
        # Save checkpoint
        save_checkpoint(
            model=self.model.module if hasattr(self.model, "module") else self.model,
            optimizer=self.optimizer if self.config.save_optimizer else None,
            scheduler=self.scheduler if self.config.save_scheduler else None,
            epoch=self.epoch,
            step=self.global_step,
            loss=self.best_metric,
            checkpoint_dir=self.config.checkpoint_dir,
            checkpoint_name=checkpoint_name,
        )
    
    def save_model(self, output_dir: str) -> None:
        """Save model to directory."""
        # Skip saving on non-master process in distributed training
        if self.config.distributed_training and dist.get_rank() != 0:
            return
        
        # Get model to save
        model_to_save = self.model.module if hasattr(self.model, "module") else self.model
        
        # Save model
        model_to_save.save_pretrained(output_dir)
        
        # Save tokenizer if available
        if self.tokenizer is not None:
            self.tokenizer.save_pretrained(output_dir)
        
        # Save training config
        self.config.save(os.path.join(output_dir, "training_config.json"))