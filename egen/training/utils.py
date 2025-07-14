"""Training utilities for the EGen platform."""

import os
import random
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch
from torch.optim import Optimizer
from torch.optim.lr_scheduler import LambdaLR

from egen.training.config import TrainingConfig


def set_seed(seed: int) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def get_optimizer(
    model: torch.nn.Module,
    config: TrainingConfig,
) -> Optimizer:
    """Get optimizer for training."""
    # Prepare optimizer parameters
    no_decay = ["bias", "LayerNorm.weight"]
    optimizer_grouped_parameters = [
        {
            "params": [
                p for n, p in model.named_parameters()
                if not any(nd in n for nd in no_decay) and p.requires_grad
            ],
            "weight_decay": config.weight_decay,
        },
        {
            "params": [
                p for n, p in model.named_parameters()
                if any(nd in n for nd in no_decay) and p.requires_grad
            ],
            "weight_decay": 0.0,
        },
    ]
    
    # Create optimizer
    if config.adafactor:
        try:
            from transformers.optimization import Adafactor
            optimizer = Adafactor(
                optimizer_grouped_parameters,
                lr=config.learning_rate,
                scale_parameter=False,
                relative_step=False,
            )
        except ImportError:
            raise ImportError(
                "Please install transformers to use Adafactor optimizer: "
                "pip install transformers"
            )
    else:
        optimizer = torch.optim.AdamW(
            optimizer_grouped_parameters,
            lr=config.learning_rate,
            betas=(config.adam_beta1, config.adam_beta2),
            eps=config.adam_epsilon,
        )
    
    return optimizer


def get_scheduler(
    optimizer: Optimizer,
    num_training_steps: int,
    config: TrainingConfig,
) -> LambdaLR:
    """Get learning rate scheduler."""
    # Get warmup steps
    warmup_steps = config.warmup_steps
    if config.warmup_ratio > 0:
        warmup_steps = int(num_training_steps * config.warmup_ratio)
    
    # Create scheduler
    if config.lr_scheduler_type == "linear":
        return get_linear_schedule_with_warmup(
            optimizer, warmup_steps, num_training_steps
        )
    elif config.lr_scheduler_type == "cosine":
        return get_cosine_schedule_with_warmup(
            optimizer, warmup_steps, num_training_steps
        )
    elif config.lr_scheduler_type == "cosine_with_restarts":
        return get_cosine_with_hard_restarts_schedule_with_warmup(
            optimizer, warmup_steps, num_training_steps
        )
    elif config.lr_scheduler_type == "polynomial":
        return get_polynomial_decay_schedule_with_warmup(
            optimizer, warmup_steps, num_training_steps
        )
    elif config.lr_scheduler_type == "constant":
        return get_constant_schedule_with_warmup(
            optimizer, warmup_steps
        )
    elif config.lr_scheduler_type == "constant_with_warmup":
        return get_constant_schedule_with_warmup(
            optimizer, warmup_steps
        )
    else:
        raise ValueError(
            f"Unknown scheduler type: {config.lr_scheduler_type}. "
            "Available types: linear, cosine, cosine_with_restarts, "
            "polynomial, constant, constant_with_warmup"
        )


def get_linear_schedule_with_warmup(
    optimizer: Optimizer,
    num_warmup_steps: int,
    num_training_steps: int,
    last_epoch: int = -1,
) -> LambdaLR:
    """Create a schedule with a learning rate that decreases linearly after
    linearly increasing during a warmup period.
    """
    
    def lr_lambda(current_step: int) -> float:
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        return max(
            0.0,
            float(num_training_steps - current_step) / float(max(1, num_training_steps - num_warmup_steps))
        )
    
    return LambdaLR(optimizer, lr_lambda, last_epoch)


def get_cosine_schedule_with_warmup(
    optimizer: Optimizer,
    num_warmup_steps: int,
    num_training_steps: int,
    num_cycles: float = 0.5,
    last_epoch: int = -1,
) -> LambdaLR:
    """Create a schedule with a learning rate that decreases following the
    values of the cosine function between the initial lr set in the optimizer to 0,
    after a warmup period during which it increases linearly between 0 and the
    initial lr set in the optimizer.
    """
    
    def lr_lambda(current_step: int) -> float:
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        progress = float(current_step - num_warmup_steps) / float(max(1, num_training_steps - num_warmup_steps))
        return max(0.0, 0.5 * (1.0 + np.cos(np.pi * float(num_cycles) * 2.0 * progress)))
    
    return LambdaLR(optimizer, lr_lambda, last_epoch)


def get_cosine_with_hard_restarts_schedule_with_warmup(
    optimizer: Optimizer,
    num_warmup_steps: int,
    num_training_steps: int,
    num_cycles: int = 1,
    last_epoch: int = -1,
) -> LambdaLR:
    """Create a schedule with a learning rate that decreases following the
    values of the cosine function between the initial lr set in the optimizer to 0,
    with several hard restarts, after a warmup period during which it increases
    linearly between 0 and the initial lr set in the optimizer.
    """
    
    def lr_lambda(current_step: int) -> float:
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        progress = float(current_step - num_warmup_steps) / float(max(1, num_training_steps - num_warmup_steps))
        if progress >= 1.0:
            return 0.0
        return max(0.0, 0.5 * (1.0 + np.cos(np.pi * ((float(num_cycles) * progress) % 1.0))))
    
    return LambdaLR(optimizer, lr_lambda, last_epoch)


def get_polynomial_decay_schedule_with_warmup(
    optimizer: Optimizer,
    num_warmup_steps: int,
    num_training_steps: int,
    lr_end: float = 1e-7,
    power: float = 1.0,
    last_epoch: int = -1,
) -> LambdaLR:
    """Create a schedule with a learning rate that decreases as a polynomial decay
    from the initial lr set in the optimizer to end lr defined by `lr_end`,
    after a warmup period during which it increases linearly from 0 to the
    initial lr set in the optimizer.
    """
    
    def lr_lambda(current_step: int) -> float:
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        elif current_step > num_training_steps:
            return lr_end / optimizer.defaults["lr"]
        else:
            lr_range = optimizer.defaults["lr"] - lr_end
            decay_steps = num_training_steps - num_warmup_steps
            pct_remaining = 1 - float(current_step - num_warmup_steps) / float(decay_steps)
            return (lr_end + lr_range * (pct_remaining ** power)) / optimizer.defaults["lr"]
    
    return LambdaLR(optimizer, lr_lambda, last_epoch)


def get_constant_schedule_with_warmup(
    optimizer: Optimizer,
    num_warmup_steps: int,
    last_epoch: int = -1,
) -> LambdaLR:
    """Create a schedule with a constant learning rate preceded by a warmup
    period during which the learning rate increases linearly between 0 and the
    initial lr set in the optimizer.
    """
    
    def lr_lambda(current_step: int) -> float:
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        return 1.0
    
    return LambdaLR(optimizer, lr_lambda, last_epoch)


def get_constant_schedule(
    optimizer: Optimizer,
    last_epoch: int = -1,
) -> LambdaLR:
    """Create a schedule with a constant learning rate."""
    return LambdaLR(optimizer, lambda _: 1.0, last_epoch)


def save_checkpoint(
    model: torch.nn.Module,
    optimizer: Optional[Optimizer] = None,
    scheduler: Optional[LambdaLR] = None,
    epoch: int = 0,
    step: int = 0,
    loss: float = 0.0,
    metrics: Optional[Dict[str, float]] = None,
    checkpoint_dir: str = "./checkpoints",
    checkpoint_name: str = "checkpoint",
) -> str:
    """Save model checkpoint."""
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Create checkpoint path
    checkpoint_path = os.path.join(checkpoint_dir, f"{checkpoint_name}_{epoch}_{step}.pt")
    
    # Prepare checkpoint data
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "epoch": epoch,
        "step": step,
        "loss": loss,
    }
    
    # Add optimizer state
    if optimizer is not None:
        checkpoint["optimizer_state_dict"] = optimizer.state_dict()
    
    # Add scheduler state
    if scheduler is not None:
        checkpoint["scheduler_state_dict"] = scheduler.state_dict()
    
    # Add metrics
    if metrics is not None:
        checkpoint["metrics"] = metrics
    
    # Save checkpoint
    torch.save(checkpoint, checkpoint_path)
    
    return checkpoint_path


def load_checkpoint(
    checkpoint_path: str,
    model: torch.nn.Module,
    optimizer: Optional[Optimizer] = None,
    scheduler: Optional[LambdaLR] = None,
    device: Optional[torch.device] = None,
) -> Tuple[int, int, float, Optional[Dict[str, float]]]:
    """Load model checkpoint."""
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device or "cpu")
    
    # Load model state
    model.load_state_dict(checkpoint["model_state_dict"])
    
    # Load optimizer state
    if optimizer is not None and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    
    # Load scheduler state
    if scheduler is not None and "scheduler_state_dict" in checkpoint:
        scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
    
    # Get checkpoint info
    epoch = checkpoint.get("epoch", 0)
    step = checkpoint.get("step", 0)
    loss = checkpoint.get("loss", 0.0)
    metrics = checkpoint.get("metrics", None)
    
    return epoch, step, loss, metrics


def get_latest_checkpoint(checkpoint_dir: str) -> Optional[str]:
    """Get the latest checkpoint in a directory."""
    if not os.path.exists(checkpoint_dir):
        return None
    
    # Get all checkpoint files
    checkpoints = [f for f in os.listdir(checkpoint_dir) if f.endswith(".pt")]
    
    if not checkpoints:
        return None
    
    # Sort by modification time
    checkpoints.sort(key=lambda x: os.path.getmtime(os.path.join(checkpoint_dir, x)), reverse=True)
    
    return os.path.join(checkpoint_dir, checkpoints[0])