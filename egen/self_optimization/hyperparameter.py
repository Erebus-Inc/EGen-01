"""Hyperparameter tuning for the EGen platform."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import optuna
from optuna.trial import Trial

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class HyperparameterTuner:
    """Hyperparameter tuner for the EGen platform.
    
    This class is responsible for tuning hyperparameters for optimal model performance
    using Optuna.
    """

    def __init__(
        self,
        study_name: str = "egen_hyperparameter_tuning",
        storage: Optional[str] = None,
        direction: str = "minimize",
        n_trials: int = 100,
        timeout: Optional[int] = None,  # seconds
        n_jobs: int = 1,
        save_dir: str = "./hyperparameter_tuning",
    ):
        """Initialize the hyperparameter tuner.
        
        Args:
            study_name: Name of the Optuna study
            storage: Optuna storage URL (e.g., "sqlite:///optuna.db")
            direction: Optimization direction ("minimize" or "maximize")
            n_trials: Number of trials to run
            timeout: Timeout in seconds
            n_jobs: Number of parallel jobs
            save_dir: Directory to save results
        """
        self.study_name = study_name
        self.storage = storage
        self.direction = direction
        self.n_trials = n_trials
        self.timeout = timeout
        self.n_jobs = n_jobs
        self.save_dir = save_dir
        
        # Create save directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Initialize study
        self.study = optuna.create_study(
            study_name=study_name,
            storage=storage,
            direction=direction,
            load_if_exists=True,
        )
        
        # Best parameters and value
        self.best_params = None
        self.best_value = None
    
    def define_search_space(self, trial: Trial) -> Dict[str, Any]:
        """Define the search space for hyperparameters.
        
        This method should be overridden by subclasses or replaced with a custom function
        when calling `tune`.
        
        Args:
            trial: Optuna trial object
            
        Returns:
            Dictionary of hyperparameters
        """
        params = {
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 1e-2, log=True),
            "batch_size": trial.suggest_categorical("batch_size", [16, 32, 64, 128]),
            "num_layers": trial.suggest_int("num_layers", 12, 36, step=12),
            "hidden_size": trial.suggest_categorical("hidden_size", [768, 1024, 2048, 4096]),
            "num_heads": trial.suggest_categorical("num_heads", [12, 16, 32]),
            "dropout": trial.suggest_float("dropout", 0.0, 0.5),
            "weight_decay": trial.suggest_float("weight_decay", 1e-5, 1e-1, log=True),
            "warmup_steps": trial.suggest_int("warmup_steps", 100, 2000),
            "gradient_accumulation_steps": trial.suggest_int("gradient_accumulation_steps", 1, 8),
            "gradient_clip_val": trial.suggest_float("gradient_clip_val", 0.1, 2.0),
        }
        return params
    
    def objective(self, trial: Trial) -> float:
        """Objective function for hyperparameter tuning.
        
        This method should be overridden by subclasses or replaced with a custom function
        when calling `tune`.
        
        Args:
            trial: Optuna trial object
            
        Returns:
            Objective value to minimize or maximize
        """
        # Get hyperparameters for this trial
        params = self.define_search_space(trial)
        
        # This is a placeholder for actual model training and evaluation
        # In a real implementation, this would train a model with the given hyperparameters
        # and return a validation metric
        return 0.0
    
    def tune(
        self,
        objective_func: Optional[Callable[[Trial], float]] = None,
        search_space_func: Optional[Callable[[Trial], Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Run hyperparameter tuning.
        
        Args:
            objective_func: Custom objective function
            search_space_func: Custom search space function
            
        Returns:
            Dictionary with best hyperparameters
        """
        # Use custom functions if provided
        objective = objective_func if objective_func is not None else self.objective
        
        if search_space_func is not None:
            self.define_search_space = search_space_func
        
        # Run optimization
        logger.info(f"Starting hyperparameter tuning with {self.n_trials} trials...")
        self.study.optimize(
            objective,
            n_trials=self.n_trials,
            timeout=self.timeout,
            n_jobs=self.n_jobs,
        )
        
        # Get best parameters and value
        self.best_params = self.study.best_params
        self.best_value = self.study.best_value
        
        logger.info(f"Best value: {self.best_value}")
        logger.info(f"Best hyperparameters: {self.best_params}")
        
        # Save results
        self._save_results()
        
        return self.best_params
    
    def _save_results(self) -> None:
        """Save tuning results to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = os.path.join(self.save_dir, f"results_{timestamp}.json")
        
        results = {
            "study_name": self.study_name,
            "direction": self.direction,
            "n_trials": self.n_trials,
            "best_value": self.best_value,
            "best_params": self.best_params,
            "timestamp": timestamp,
        }
        
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved results to {results_path}")
    
    def get_best_params(self) -> Dict[str, Any]:
        """Get the best hyperparameters found during tuning.
        
        Returns:
            Dictionary with best hyperparameters
        """
        if self.best_params is None:
            logger.warning("No tuning has been performed yet.")
            return {}
        
        return self.best_params
    
    def load_best_params(self, path: str) -> Dict[str, Any]:
        """Load best hyperparameters from a JSON file.
        
        Args:
            path: Path to JSON file
            
        Returns:
            Dictionary with best hyperparameters
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                results = json.load(f)
            
            self.best_params = results["best_params"]
            self.best_value = results["best_value"]
            
            logger.info(f"Loaded best hyperparameters from {path}")
            
            return self.best_params
        except Exception as e:
            logger.error(f"Error loading best hyperparameters: {e}", exc_info=True)
            return {}


class THL150HyperparameterTuner(HyperparameterTuner):
    """Hyperparameter tuner specifically for the THL-150 model."""

    def define_search_space(self, trial: Trial) -> Dict[str, Any]:
        """Define the search space for THL-150 hyperparameters.
        
        Args:
            trial: Optuna trial object
            
        Returns:
            Dictionary of hyperparameters
        """
        params = {
            # Learning rate and schedule
            "learning_rate": trial.suggest_float("learning_rate", 1e-5, 5e-4, log=True),
            "warmup_steps": trial.suggest_int("warmup_steps", 500, 2000),
            "weight_decay": trial.suggest_float("weight_decay", 0.01, 0.1),
            
            # Batch size and gradient accumulation
            "batch_size": trial.suggest_categorical("batch_size", [16, 32, 64]),
            "gradient_accumulation_steps": trial.suggest_int("gradient_accumulation_steps", 1, 8),
            "gradient_clip_val": trial.suggest_float("gradient_clip_val", 0.5, 1.5),
            
            # Domain routing
            "domain_router_hidden_size": trial.suggest_categorical("domain_router_hidden_size", [256, 512, 1024]),
            "domain_router_dropout": trial.suggest_float("domain_router_dropout", 0.0, 0.3),
            "domain_router_threshold": trial.suggest_float("domain_router_threshold", 0.3, 0.7),
            
            # Sparse routing
            "sparse_routing_factor": trial.suggest_float("sparse_routing_factor", 0.1, 0.5),
            "sparse_routing_topk": trial.suggest_int("sparse_routing_topk", 3, 10),
            
            # Attention
            "attention_dropout": trial.suggest_float("attention_dropout", 0.0, 0.2),
            "use_flash_attention": trial.suggest_categorical("use_flash_attention", [True, False]),
            
            # MLP
            "mlp_ratio": trial.suggest_float("mlp_ratio", 2.0, 4.0),
            "mlp_dropout": trial.suggest_float("mlp_dropout", 0.0, 0.2),
            
            # Optimization
            "use_adafactor": trial.suggest_categorical("use_adafactor", [True, False]),
            "use_8bit_optimizer": trial.suggest_categorical("use_8bit_optimizer", [True, False]),
        }
        return params
    
    def objective(self, trial: Trial) -> float:
        """Objective function for THL-150 hyperparameter tuning.
        
        Args:
            trial: Optuna trial object
            
        Returns:
            Validation loss
        """
        from egen.model import THL150
        from egen.model.config import ModelConfig
        from egen.training import Trainer, TrainingConfig
        
        # Get hyperparameters for this trial
        params = self.define_search_space(trial)
        
        # Create model config
        model_config = ModelConfig(
            num_layers=150,  # Fixed for THL-150
            hidden_size=4096,  # Fixed for THL-150
            num_heads=32,  # Fixed for THL-150
            vocab_size=32000,  # Fixed for THL-150
            max_position_embeddings=32768,  # Fixed for THL-150
            domain_router_hidden_size=params["domain_router_hidden_size"],
            domain_router_dropout=params["domain_router_dropout"],
            domain_router_threshold=params["domain_router_threshold"],
            sparse_routing_factor=params["sparse_routing_factor"],
            sparse_routing_topk=params["sparse_routing_topk"],
            attention_dropout=params["attention_dropout"],
            use_flash_attention=params["use_flash_attention"],
            mlp_ratio=params["mlp_ratio"],
            mlp_dropout=params["mlp_dropout"],
        )
        
        # Create training config
        training_config = TrainingConfig(
            batch_size=params["batch_size"],
            learning_rate=params["learning_rate"],
            weight_decay=params["weight_decay"],
            warmup_steps=params["warmup_steps"],
            gradient_accumulation_steps=params["gradient_accumulation_steps"],
            gradient_clip_val=params["gradient_clip_val"],
            use_adafactor=params["use_adafactor"],
            use_8bit_optimizer=params["use_8bit_optimizer"],
            mixed_precision="bf16",  # Always use mixed precision
            num_epochs=1,  # Use a single epoch for tuning
        )
        
        # Create model
        model = THL150(model_config)
        
        # Create trainer
        trainer = Trainer(
            model=model,
            config=training_config,
            train_dataset=None,  # Placeholder for actual dataset
            eval_dataset=None,  # Placeholder for actual dataset
            checkpoint_dir=f"./checkpoints/trial_{trial.number}",
        )
        
        # Train and evaluate
        try:
            # This is a placeholder for actual training and evaluation
            # In a real implementation, this would train the model and return validation loss
            validation_loss = 0.0
            
            return validation_loss
        except Exception as e:
            logger.error(f"Error in trial {trial.number}: {e}", exc_info=True)
            raise optuna.exceptions.TrialPruned()