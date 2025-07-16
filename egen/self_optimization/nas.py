"""Neural Architecture Search for the EGen platform."""

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


class NeuralArchitectureSearch:
    """Neural Architecture Search for the EGen platform.
    
    This class is responsible for searching for optimal neural network architectures
    using Optuna.
    """

    def __init__(
        self,
        study_name: str = "egen_nas",
        storage: Optional[str] = None,
        direction: str = "minimize",
        n_trials: int = 50,
        timeout: Optional[int] = None,  # seconds
        n_jobs: int = 1,
        save_dir: str = "./nas_results",
    ):
        """Initialize the Neural Architecture Search.
        
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
        
        # Best architecture and value
        self.best_architecture = None
        self.best_value = None
    
    def define_search_space(self, trial: Trial) -> Dict[str, Any]:
        """Define the search space for neural architecture.
        
        This method should be overridden by subclasses or replaced with a custom function
        when calling `search`.
        
        Args:
            trial: Optuna trial object
            
        Returns:
            Dictionary of architecture parameters
        """
        architecture = {
            # Layer configuration
            "num_layers": trial.suggest_int("num_layers", 12, 48, step=12),
            "hidden_size": trial.suggest_categorical("hidden_size", [768, 1024, 2048, 4096]),
            "num_heads": trial.suggest_categorical("num_heads", [12, 16, 32]),
            "mlp_ratio": trial.suggest_float("mlp_ratio", 2.0, 4.0),
            
            # Attention mechanism
            "attention_type": trial.suggest_categorical(
                "attention_type", ["vanilla", "flash", "sparse", "linear"]
            ),
            "attention_window_size": trial.suggest_categorical(
                "attention_window_size", [128, 256, 512]
            ),
            
            # Activation function
            "activation_function": trial.suggest_categorical(
                "activation_function", ["gelu", "relu", "swish", "glu"]
            ),
            
            # Normalization
            "normalization_type": trial.suggest_categorical(
                "normalization_type", ["layer_norm", "rms_norm"]
            ),
            
            # Embedding
            "embedding_type": trial.suggest_categorical(
                "embedding_type", ["learned", "rotary", "alibi"]
            ),
            
            # Domain routing
            "use_domain_routing": trial.suggest_categorical("use_domain_routing", [True, False]),
            "num_domains": trial.suggest_int("num_domains", 4, 16) if trial.params.get("use_domain_routing", False) else 0,
            
            # Conditional execution
            "use_conditional_execution": trial.suggest_categorical("use_conditional_execution", [True, False]),
            
            # Sparse routing
            "use_sparse_routing": trial.suggest_categorical("use_sparse_routing", [True, False]),
            "sparse_routing_factor": trial.suggest_float("sparse_routing_factor", 0.1, 0.5) if trial.params.get("use_sparse_routing", False) else 0.0,
            "sparse_routing_topk": trial.suggest_int("sparse_routing_topk", 3, 10) if trial.params.get("use_sparse_routing", False) else 0,
        }
        return architecture
    
    def objective(self, trial: Trial) -> float:
        """Objective function for neural architecture search.
        
        This method should be overridden by subclasses or replaced with a custom function
        when calling `search`.
        
        Args:
            trial: Optuna trial object
            
        Returns:
            Objective value to minimize or maximize
        """
        # Get architecture for this trial
        architecture = self.define_search_space(trial)
        
        # This is a placeholder for actual model training and evaluation
        # In a real implementation, this would train a model with the given architecture
        # and return a validation metric
        return 0.0
    
    def search(
        self,
        objective_func: Optional[Callable[[Trial], float]] = None,
        search_space_func: Optional[Callable[[Trial], Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Run neural architecture search.
        
        Args:
            objective_func: Custom objective function
            search_space_func: Custom search space function
            
        Returns:
            Dictionary with best architecture
        """
        # Use custom functions if provided
        objective = objective_func if objective_func is not None else self.objective
        
        if search_space_func is not None:
            self.define_search_space = search_space_func
        
        # Run optimization
        logger.info(f"Starting neural architecture search with {self.n_trials} trials...")
        self.study.optimize(
            objective,
            n_trials=self.n_trials,
            timeout=self.timeout,
            n_jobs=self.n_jobs,
        )
        
        # Get best architecture and value
        self.best_architecture = self.study.best_params
        self.best_value = self.study.best_value
        
        logger.info(f"Best value: {self.best_value}")
        logger.info(f"Best architecture: {self.best_architecture}")
        
        # Save results
        self._save_results()
        
        return self.best_architecture
    
    def _save_results(self) -> None:
        """Save search results to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = os.path.join(self.save_dir, f"results_{timestamp}.json")
        
        results = {
            "study_name": self.study_name,
            "direction": self.direction,
            "n_trials": self.n_trials,
            "best_value": self.best_value,
            "best_architecture": self.best_architecture,
            "timestamp": timestamp,
        }
        
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved results to {results_path}")
    
    def get_best_architecture(self) -> Dict[str, Any]:
        """Get the best architecture found during search.
        
        Returns:
            Dictionary with best architecture
        """
        if self.best_architecture is None:
            logger.warning("No search has been performed yet.")
            return {}
        
        return self.best_architecture
    
    def load_best_architecture(self, path: str) -> Dict[str, Any]:
        """Load best architecture from a JSON file.
        
        Args:
            path: Path to JSON file
            
        Returns:
            Dictionary with best architecture
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                results = json.load(f)
            
            self.best_architecture = results["best_architecture"]
            self.best_value = results["best_value"]
            
            logger.info(f"Loaded best architecture from {path}")
            
            return self.best_architecture
        except Exception as e:
            logger.error(f"Error loading best architecture: {e}", exc_info=True)
            return {}


class THL150NeuralArchitectureSearch(NeuralArchitectureSearch):
    """Neural Architecture Search specifically for the THL-150 model."""

    def define_search_space(self, trial: Trial) -> Dict[str, Any]:
        """Define the search space for THL-150 architecture.
        
        Args:
            trial: Optuna trial object
            
        Returns:
            Dictionary of architecture parameters
        """
        # For THL-150, we keep the core structure fixed (150 layers, 14B parameters)
        # but search for optimal configurations of components
        architecture = {
            # Fixed parameters
            "num_layers": 150,  # Fixed for THL-150
            "hidden_size": 4096,  # Fixed for THL-150
            "num_heads": 32,  # Fixed for THL-150
            
            # Attention mechanism
            "attention_type": trial.suggest_categorical(
                "attention_type", ["flash", "sparse", "linear"]
            ),
            
            # Activation function
            "activation_function": trial.suggest_categorical(
                "activation_function", ["gelu", "swish", "glu"]
            ),
            
            # Normalization
            "normalization_type": trial.suggest_categorical(
                "normalization_type", ["layer_norm", "rms_norm"]
            ),
            
            # Embedding
            "embedding_type": trial.suggest_categorical(
                "embedding_type", ["rotary", "alibi"]
            ),
            
            # Domain routing
            "num_domains": trial.suggest_int("num_domains", 4, 16),
            "domain_router_hidden_size": trial.suggest_categorical(
                "domain_router_hidden_size", [256, 512, 1024]
            ),
            "domain_router_dropout": trial.suggest_float("domain_router_dropout", 0.0, 0.3),
            "domain_router_threshold": trial.suggest_float("domain_router_threshold", 0.3, 0.7),
            
            # Conditional execution
            "conditional_execution_strategy": trial.suggest_categorical(
                "conditional_execution_strategy", ["threshold", "topk", "hybrid"]
            ),
            
            # Sparse routing
            "sparse_routing_factor": trial.suggest_float("sparse_routing_factor", 0.1, 0.5),
            "sparse_routing_topk": trial.suggest_int("sparse_routing_topk", 3, 10),
            
            # MLP configuration
            "mlp_ratio": trial.suggest_float("mlp_ratio", 2.0, 4.0),
            "mlp_activation": trial.suggest_categorical(
                "mlp_activation", ["gelu", "swish", "glu"]
            ),
            
            # Layer distribution
            "layer_distribution": trial.suggest_categorical(
                "layer_distribution", ["uniform", "progressive", "bottleneck"]
            ),
        }
        return architecture
    
    def objective(self, trial: Trial) -> float:
        """Objective function for THL-150 neural architecture search.
        
        Args:
            trial: Optuna trial object
            
        Returns:
            Validation perplexity
        """
        from egen.model import THL150
        from egen.model.config import ModelConfig
        from egen.training import Trainer, TrainingConfig
        
        # Get architecture for this trial
        architecture = self.define_search_space(trial)
        
        # Create model config
        model_config = ModelConfig(
            num_layers=architecture["num_layers"],
            hidden_size=architecture["hidden_size"],
            num_heads=architecture["num_heads"],
            vocab_size=32000,  # Fixed
            max_position_embeddings=32768,  # Fixed
            attention_type=architecture["attention_type"],
            activation_function=architecture["activation_function"],
            normalization_type=architecture["normalization_type"],
            embedding_type=architecture["embedding_type"],
            num_domains=architecture["num_domains"],
            domain_router_hidden_size=architecture["domain_router_hidden_size"],
            domain_router_dropout=architecture["domain_router_dropout"],
            domain_router_threshold=architecture["domain_router_threshold"],
            conditional_execution_strategy=architecture["conditional_execution_strategy"],
            sparse_routing_factor=architecture["sparse_routing_factor"],
            sparse_routing_topk=architecture["sparse_routing_topk"],
            mlp_ratio=architecture["mlp_ratio"],
            mlp_activation=architecture["mlp_activation"],
            layer_distribution=architecture["layer_distribution"],
        )
        
        # Create training config
        training_config = TrainingConfig(
            batch_size=32,  # Fixed for architecture search
            learning_rate=1e-4,  # Fixed for architecture search
            weight_decay=0.1,  # Fixed for architecture search
            warmup_steps=1000,  # Fixed for architecture search
            gradient_accumulation_steps=4,  # Fixed for architecture search
            gradient_clip_val=1.0,  # Fixed for architecture search
            mixed_precision="bf16",  # Always use mixed precision
            num_epochs=1,  # Use a single epoch for architecture search
        )
        
        # Create model
        model = THL150(model_config)
        
        # Create trainer
        trainer = Trainer(
            model=model,
            config=training_config,
            train_dataset=None,  # Placeholder for actual dataset
            eval_dataset=None,  # Placeholder for actual dataset
            checkpoint_dir=f"./checkpoints/nas_trial_{trial.number}",
        )
        
        # Train and evaluate
        try:
            # Train and evaluate
            trainer.train()
            eval_results = trainer.evaluate()
            return eval_results.get('validation_perplexity', 100.0)
        except Exception as e:
            logger.error(f"Error in trial {trial.number}: {e}", exc_info=True)
            raise optuna.exceptions.TrialPruned()