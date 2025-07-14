"""Self-Optimization System for the EGen platform.

This package provides components for automatically optimizing the THL-150 model
through neural architecture search, hyperparameter tuning, pruning, and quantization.

Components:
- Neural Architecture Search: Searches for optimal neural network architectures
- Hyperparameter Tuner: Optimizes model hyperparameters
- Pruning Optimizer: Reduces model size through weight pruning
- Quantization Optimizer: Reduces model size through quantization
- Self-Optimization Agent: Coordinates optimization techniques
"""

from egen.self_optimization.agent import (
    SelfOptimizationAgent,
    THL150SelfOptimizationAgent,
    create_agent,
)
from egen.self_optimization.hyperparameter import (
    HyperparameterTuner,
    THL150HyperparameterTuner,
)
from egen.self_optimization.nas import (
    NeuralArchitectureSearch,
    THL150NeuralArchitectureSearch,
)
from egen.self_optimization.pruning import (
    PruningOptimizer,
    THL150PruningOptimizer,
)
from egen.self_optimization.quantization import (
    QuantizationOptimizer,
    THL150QuantizationOptimizer,
)

__all__ = [
    # Agent
    "SelfOptimizationAgent",
    "THL150SelfOptimizationAgent",
    "create_agent",
    
    # Hyperparameter Tuning
    "HyperparameterTuner",
    "THL150HyperparameterTuner",
    
    # Neural Architecture Search
    "NeuralArchitectureSearch",
    "THL150NeuralArchitectureSearch",
    
    # Pruning
    "PruningOptimizer",
    "THL150PruningOptimizer",
    
    # Quantization
    "QuantizationOptimizer",
    "THL150QuantizationOptimizer",
]