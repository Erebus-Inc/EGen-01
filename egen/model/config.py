"""Configuration for the THL-150 transformer model."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union


@dataclass
class ModelConfig:
    """Configuration for the THL-150 transformer model."""

    # Model architecture
    num_layers: int = 150
    hidden_size: int = 4096
    intermediate_size: int = 11008
    num_attention_heads: int = 32
    num_key_value_heads: int = 32
    max_position_embeddings: int = 32768
    vocab_size: int = 32000
    activation_function: str = "silu"
    layer_norm_epsilon: float = 1e-5
    initializer_range: float = 0.02
    use_cache: bool = True
    pad_token_id: int = 0
    bos_token_id: int = 1
    eos_token_id: int = 2
    tie_word_embeddings: bool = False
    rope_theta: float = 10000.0
    attention_bias: bool = False
    
    # Domain routing
    domain_routing: bool = True
    domain_types: List[str] = field(
        default_factory=lambda: ["general", "code", "math", "security", "it"]
    )
    domain_layer_allocation: Dict[str, List[int]] = field(default_factory=dict)
    
    # Conditional execution
    conditional_execution: bool = True
    layer_activation_threshold: float = 0.5
    
    # Sparse routing
    sparse_routing: bool = True
    sparsity_factor: float = 0.8
    
    # Training
    gradient_checkpointing: bool = False
    use_flash_attention: bool = True
    use_mixed_precision: bool = True
    
    def __post_init__(self):
        """Initialize domain layer allocation if not provided."""
        if not self.domain_layer_allocation and self.domain_routing:
            # Allocate layers to domains
            layers_per_domain = self.num_layers // len(self.domain_types)
            remaining_layers = self.num_layers % len(self.domain_types)
            
            start_idx = 0
            for i, domain in enumerate(self.domain_types):
                end_idx = start_idx + layers_per_domain
                if i < remaining_layers:
                    end_idx += 1
                
                self.domain_layer_allocation[domain] = list(range(start_idx, end_idx))
                start_idx = end_idx
    
    @classmethod
    def from_pretrained(cls, model_name_or_path: str) -> "ModelConfig":
        """Load configuration from a pretrained model."""
        # This would load configuration from a file or API
        # For now, return default config
        return cls()
    
    def to_dict(self) -> Dict[str, Union[int, float, bool, List[str], Dict[str, List[int]]]]:
        """Convert configuration to dictionary."""
        return {
            "num_layers": self.num_layers,
            "hidden_size": self.hidden_size,
            "intermediate_size": self.intermediate_size,
            "num_attention_heads": self.num_attention_heads,
            "num_key_value_heads": self.num_key_value_heads,
            "max_position_embeddings": self.max_position_embeddings,
            "vocab_size": self.vocab_size,
            "activation_function": self.activation_function,
            "layer_norm_epsilon": self.layer_norm_epsilon,
            "initializer_range": self.initializer_range,
            "use_cache": self.use_cache,
            "pad_token_id": self.pad_token_id,
            "bos_token_id": self.bos_token_id,
            "eos_token_id": self.eos_token_id,
            "tie_word_embeddings": self.tie_word_embeddings,
            "rope_theta": self.rope_theta,
            "attention_bias": self.attention_bias,
            "domain_routing": self.domain_routing,
            "domain_types": self.domain_types,
            "domain_layer_allocation": self.domain_layer_allocation,
            "conditional_execution": self.conditional_execution,
            "layer_activation_threshold": self.layer_activation_threshold,
            "sparse_routing": self.sparse_routing,
            "sparsity_factor": self.sparsity_factor,
            "gradient_checkpointing": self.gradient_checkpointing,
            "use_flash_attention": self.use_flash_attention,
            "use_mixed_precision": self.use_mixed_precision,
        }
    
    def save_pretrained(self, save_directory: str) -> None:
        """Save configuration to a directory."""
        import os
        import json
        
        os.makedirs(save_directory, exist_ok=True)
        config_file = os.path.join(save_directory, "config.json")
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)