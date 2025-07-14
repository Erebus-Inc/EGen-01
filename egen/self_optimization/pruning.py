"""Pruning Optimizer for the EGen platform."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class PruningOptimizer:
    """Pruning Optimizer for the EGen platform.
    
    This class is responsible for pruning neural networks to reduce their size
    and improve inference speed while maintaining performance.
    """

    def __init__(
        self,
        model: nn.Module,
        save_dir: str = "./pruning_results",
        target_sparsity: float = 0.5,
        pruning_method: str = "magnitude",
        pruning_schedule: str = "iterative",
        importance_metric: str = "weight",
        fine_tuning_steps: int = 1000,
        evaluation_func: Optional[Callable[[nn.Module], float]] = None,
    ):
        """Initialize the Pruning Optimizer.
        
        Args:
            model: PyTorch model to prune
            save_dir: Directory to save results
            target_sparsity: Target sparsity ratio (0.0 to 1.0)
            pruning_method: Method for pruning ("magnitude", "structured", "movement", "lottery")
            pruning_schedule: Schedule for pruning ("one_shot", "iterative", "gradual")
            importance_metric: Metric for determining importance ("weight", "gradient", "activation")
            fine_tuning_steps: Number of fine-tuning steps after pruning
            evaluation_func: Function to evaluate model performance
        """
        self.model = model
        self.save_dir = save_dir
        self.target_sparsity = target_sparsity
        self.pruning_method = pruning_method
        self.pruning_schedule = pruning_schedule
        self.importance_metric = importance_metric
        self.fine_tuning_steps = fine_tuning_steps
        self.evaluation_func = evaluation_func
        
        # Create save directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Initialize pruning state
        self.current_sparsity = 0.0
        self.pruning_step = 0
        self.pruning_history = []
        self.masks = {}
        self.original_weights = {}
        
        # Store original model performance
        self.original_performance = None
        if self.evaluation_func is not None:
            self.original_performance = self.evaluation_func(self.model)
            logger.info(f"Original model performance: {self.original_performance}")
    
    def _compute_importance_scores(self, module: nn.Module, name: str) -> torch.Tensor:
        """Compute importance scores for weights in a module.
        
        Args:
            module: PyTorch module
            name: Name of the module
            
        Returns:
            Tensor of importance scores
        """
        if self.importance_metric == "weight":
            # Use absolute weight values as importance scores
            if hasattr(module, "weight") and module.weight is not None:
                return torch.abs(module.weight.data)
            return None
        elif self.importance_metric == "gradient":
            # Use absolute gradient values as importance scores
            if hasattr(module, "weight") and module.weight is not None and module.weight.grad is not None:
                return torch.abs(module.weight.grad.data)
            return None
        elif self.importance_metric == "activation":
            # This would require tracking activations during forward pass
            # For simplicity, we'll use weight values as a fallback
            if hasattr(module, "weight") and module.weight is not None:
                return torch.abs(module.weight.data)
            return None
        else:
            raise ValueError(f"Unknown importance metric: {self.importance_metric}")
    
    def _create_mask(self, importance_scores: torch.Tensor, sparsity: float) -> torch.Tensor:
        """Create a binary mask based on importance scores and target sparsity.
        
        Args:
            importance_scores: Tensor of importance scores
            sparsity: Target sparsity for this layer
            
        Returns:
            Binary mask tensor (1 for keep, 0 for prune)
        """
        if self.pruning_method == "magnitude":
            # Magnitude pruning: keep weights with highest absolute values
            threshold = torch.quantile(importance_scores.flatten(), sparsity)
            return (importance_scores > threshold).float()
        elif self.pruning_method == "structured":
            # Structured pruning: prune entire channels/filters
            # For simplicity, we'll implement channel pruning for Conv2d layers
            if len(importance_scores.shape) == 4:  # Conv2d weights
                channel_importance = importance_scores.mean(dim=(1, 2, 3))
                threshold = torch.quantile(channel_importance, sparsity)
                channel_mask = (channel_importance > threshold).float()
                return channel_mask.view(-1, 1, 1, 1).expand_as(importance_scores)
            else:
                # Fall back to magnitude pruning for other layer types
                threshold = torch.quantile(importance_scores.flatten(), sparsity)
                return (importance_scores > threshold).float()
        elif self.pruning_method == "movement":
            # Movement pruning: compare current weights to original weights
            if importance_scores.shape in self.original_weights:
                movement = torch.abs(importance_scores - self.original_weights[importance_scores.shape])
                threshold = torch.quantile(movement.flatten(), 1 - sparsity)  # Keep weights that moved the most
                return (movement > threshold).float()
            else:
                # Fall back to magnitude pruning
                threshold = torch.quantile(importance_scores.flatten(), sparsity)
                return (importance_scores > threshold).float()
        elif self.pruning_method == "lottery":
            # Lottery ticket hypothesis: randomly prune and reset to original weights
            mask = torch.rand_like(importance_scores) > sparsity
            return mask.float()
        else:
            raise ValueError(f"Unknown pruning method: {self.pruning_method}")
    
    def _apply_mask(self, module: nn.Module, name: str, mask: torch.Tensor) -> None:
        """Apply a pruning mask to a module's weights.
        
        Args:
            module: PyTorch module
            name: Name of the module
            mask: Binary mask tensor
        """
        if hasattr(module, "weight") and module.weight is not None:
            # Store original weights for lottery ticket hypothesis
            if module.weight.shape not in self.original_weights:
                self.original_weights[module.weight.shape] = module.weight.data.clone()
            
            # Apply mask
            module.weight.data *= mask
            
            # Store mask for future pruning steps
            self.masks[name] = mask
    
    def _should_prune_layer(self, name: str, module: nn.Module) -> bool:
        """Determine if a layer should be pruned.
        
        Args:
            name: Name of the module
            module: PyTorch module
            
        Returns:
            Boolean indicating whether to prune this layer
        """
        # Skip layers without weights
        if not hasattr(module, "weight") or module.weight is None:
            return False
        
        # Skip batch normalization layers
        if isinstance(module, (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d,
                              nn.LayerNorm, nn.GroupNorm, nn.InstanceNorm1d,
                              nn.InstanceNorm2d, nn.InstanceNorm3d)):
            return False
        
        # Skip embedding layers
        if isinstance(module, nn.Embedding):
            return False
        
        return True
    
    def prune(self) -> nn.Module:
        """Prune the model according to the specified method and schedule.
        
        Returns:
            Pruned PyTorch model
        """
        logger.info(f"Starting pruning with method: {self.pruning_method}, "
                   f"schedule: {self.pruning_schedule}, "
                   f"target sparsity: {self.target_sparsity}")
        
        if self.pruning_schedule == "one_shot":
            # One-shot pruning: prune to target sparsity in a single step
            self._prune_step(self.target_sparsity)
        elif self.pruning_schedule == "iterative":
            # Iterative pruning: prune in multiple steps
            num_steps = 5
            for step in range(num_steps):
                step_sparsity = self.target_sparsity * (step + 1) / num_steps
                self._prune_step(step_sparsity)
                if self.evaluation_func is not None:
                    performance = self.evaluation_func(self.model)
                    logger.info(f"Performance after pruning step {step+1}/{num_steps}: {performance}")
        elif self.pruning_schedule == "gradual":
            # Gradual pruning: prune a small amount, fine-tune, repeat
            num_steps = 10
            for step in range(num_steps):
                step_sparsity = self.target_sparsity * (step + 1) / num_steps
                self._prune_step(step_sparsity)
                # Fine-tune after each pruning step (placeholder)
                logger.info(f"Fine-tuning after pruning step {step+1}/{num_steps}")
                # In a real implementation, this would call a fine-tuning method
                if self.evaluation_func is not None:
                    performance = self.evaluation_func(self.model)
                    logger.info(f"Performance after pruning step {step+1}/{num_steps}: {performance}")
        else:
            raise ValueError(f"Unknown pruning schedule: {self.pruning_schedule}")
        
        # Final evaluation
        if self.evaluation_func is not None:
            final_performance = self.evaluation_func(self.model)
            logger.info(f"Final model performance after pruning: {final_performance}")
            logger.info(f"Performance change: {final_performance - self.original_performance}")
        
        # Save results
        self._save_results()
        
        return self.model
    
    def _prune_step(self, target_sparsity: float) -> None:
        """Perform a single pruning step.
        
        Args:
            target_sparsity: Target sparsity for this step
        """
        logger.info(f"Pruning step {self.pruning_step + 1} with target sparsity: {target_sparsity}")
        
        # Iterate through all modules
        for name, module in self.model.named_modules():
            if not self._should_prune_layer(name, module):
                continue
            
            # Compute importance scores
            importance_scores = self._compute_importance_scores(module, name)
            if importance_scores is None:
                continue
            
            # Create mask
            mask = self._create_mask(importance_scores, target_sparsity)
            
            # Apply mask
            self._apply_mask(module, name, mask)
        
        # Update pruning state
        self.current_sparsity = target_sparsity
        self.pruning_step += 1
        
        # Calculate actual sparsity
        total_params = 0
        pruned_params = 0
        for name, module in self.model.named_modules():
            if hasattr(module, "weight") and module.weight is not None:
                total_params += module.weight.numel()
                pruned_params += (module.weight.data == 0).sum().item()
        
        actual_sparsity = pruned_params / total_params if total_params > 0 else 0
        logger.info(f"Actual sparsity after pruning step: {actual_sparsity:.4f}")
        
        # Record pruning history
        self.pruning_history.append({
            "step": self.pruning_step,
            "target_sparsity": target_sparsity,
            "actual_sparsity": actual_sparsity,
        })
    
    def _save_results(self) -> None:
        """Save pruning results to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = os.path.join(self.save_dir, f"pruning_results_{timestamp}.json")
        
        results = {
            "pruning_method": self.pruning_method,
            "pruning_schedule": self.pruning_schedule,
            "importance_metric": self.importance_metric,
            "target_sparsity": self.target_sparsity,
            "final_sparsity": self.current_sparsity,
            "pruning_history": self.pruning_history,
            "original_performance": self.original_performance,
            "timestamp": timestamp,
        }
        
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved pruning results to {results_path}")
        
        # Save model checkpoint
        model_path = os.path.join(self.save_dir, f"pruned_model_{timestamp}.pt")
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "pruning_info": results,
        }, model_path)
        
        logger.info(f"Saved pruned model to {model_path}")
    
    def get_sparsity_info(self) -> Dict[str, Any]:
        """Get information about the current sparsity of the model.
        
        Returns:
            Dictionary with sparsity information
        """
        layer_sparsity = {}
        total_params = 0
        pruned_params = 0
        
        for name, module in self.model.named_modules():
            if hasattr(module, "weight") and module.weight is not None:
                weight = module.weight.data
                num_params = weight.numel()
                num_zeros = (weight == 0).sum().item()
                sparsity = num_zeros / num_params if num_params > 0 else 0
                
                layer_sparsity[name] = {
                    "total_params": num_params,
                    "pruned_params": num_zeros,
                    "sparsity": sparsity,
                }
                
                total_params += num_params
                pruned_params += num_zeros
        
        overall_sparsity = pruned_params / total_params if total_params > 0 else 0
        
        return {
            "overall_sparsity": overall_sparsity,
            "total_params": total_params,
            "pruned_params": pruned_params,
            "layer_sparsity": layer_sparsity,
        }


class THL150PruningOptimizer(PruningOptimizer):
    """Pruning Optimizer specifically for the THL-150 model."""

    def __init__(
        self,
        model: nn.Module,
        save_dir: str = "./pruning_results",
        target_sparsity: float = 0.3,  # Lower default sparsity for THL-150
        pruning_method: str = "structured",  # Default to structured pruning
        pruning_schedule: str = "gradual",  # Default to gradual pruning
        importance_metric: str = "weight",
        fine_tuning_steps: int = 2000,  # More fine-tuning steps
        evaluation_func: Optional[Callable[[nn.Module], float]] = None,
        domain_aware: bool = True,  # Domain-aware pruning
    ):
        """Initialize the THL-150 Pruning Optimizer.
        
        Args:
            model: THL-150 model to prune
            save_dir: Directory to save results
            target_sparsity: Target sparsity ratio (0.0 to 1.0)
            pruning_method: Method for pruning
            pruning_schedule: Schedule for pruning
            importance_metric: Metric for determining importance
            fine_tuning_steps: Number of fine-tuning steps after pruning
            evaluation_func: Function to evaluate model performance
            domain_aware: Whether to use domain-aware pruning
        """
        super().__init__(
            model=model,
            save_dir=save_dir,
            target_sparsity=target_sparsity,
            pruning_method=pruning_method,
            pruning_schedule=pruning_schedule,
            importance_metric=importance_metric,
            fine_tuning_steps=fine_tuning_steps,
            evaluation_func=evaluation_func,
        )
        self.domain_aware = domain_aware
        self.domain_importance = {}  # Store importance scores per domain
    
    def _should_prune_layer(self, name: str, module: nn.Module) -> bool:
        """Determine if a layer should be pruned in THL-150.
        
        Args:
            name: Name of the module
            module: PyTorch module
            
        Returns:
            Boolean indicating whether to prune this layer
        """
        # First apply the base class rules
        if not super()._should_prune_layer(name, module):
            return False
        
        # THL-150 specific rules
        
        # Don't prune domain router components
        if "domain_router" in name:
            return False
        
        # Don't prune the first and last few layers
        if "layers.0." in name or "layers.1." in name or "layers.2." in name:
            return False
        
        if "layers.147." in name or "layers.148." in name or "layers.149." in name:
            return False
        
        # Don't prune embedding layers
        if "embedding" in name or "embeddings" in name:
            return False
        
        return True
    
    def _compute_importance_scores(self, module: nn.Module, name: str) -> torch.Tensor:
        """Compute importance scores for weights in THL-150 modules.
        
        Args:
            module: PyTorch module
            name: Name of the module
            
        Returns:
            Tensor of importance scores
        """
        # Get base importance scores
        importance_scores = super()._compute_importance_scores(module, name)
        if importance_scores is None:
            return None
        
        # Apply domain-aware adjustments if enabled
        if self.domain_aware and hasattr(module, "domain_activation"):
            # Adjust importance based on domain activation
            domain_activation = module.domain_activation
            
            # Store domain importance for this layer
            self.domain_importance[name] = domain_activation.detach().cpu()
            
            # Scale importance scores by domain activation
            # This makes weights more important in highly activated domains
            if len(domain_activation.shape) == 1:  # [num_domains]
                # Reshape for broadcasting
                domain_activation = domain_activation.view(-1, 1, 1, 1)
            
            # Apply domain importance as a scaling factor
            importance_scores = importance_scores * domain_activation.mean()
        
        return importance_scores
    
    def prune(self) -> nn.Module:
        """Prune the THL-150 model with domain awareness.
        
        Returns:
            Pruned THL-150 model
        """
        logger.info(f"Starting THL-150 pruning with domain-aware: {self.domain_aware}")
        
        # Run a forward pass to collect domain activations if domain-aware
        if self.domain_aware:
            logger.info("Collecting domain activations for domain-aware pruning")
            # This would normally run a forward pass on representative data
            # For simplicity, we'll assume domain activations are already set
        
        # Call the base class pruning method
        return super().prune()
    
    def _save_results(self) -> None:
        """Save THL-150 pruning results to disk."""
        # Call the base class method
        super()._save_results()
        
        # Save domain importance if available
        if self.domain_aware and self.domain_importance:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain_path = os.path.join(self.save_dir, f"domain_importance_{timestamp}.pt")
            
            # Convert to numpy for easier serialization
            domain_importance_np = {}
            for name, tensor in self.domain_importance.items():
                domain_importance_np[name] = tensor.numpy()
            
            np.savez(domain_path, **domain_importance_np)
            logger.info(f"Saved domain importance to {domain_path}")