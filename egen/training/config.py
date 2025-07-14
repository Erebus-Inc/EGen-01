"""Training configuration for the EGen platform."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union


@dataclass
class TrainingConfig:
    """Configuration for training the THL-150 model."""

    # Basic training parameters
    output_dir: str = "./outputs"
    overwrite_output_dir: bool = False
    do_train: bool = True
    do_eval: bool = True
    do_predict: bool = False
    evaluation_strategy: str = "steps"
    prediction_loss_only: bool = False
    per_device_train_batch_size: int = 8
    per_device_eval_batch_size: int = 8
    gradient_accumulation_steps: int = 1
    eval_accumulation_steps: Optional[int] = None
    learning_rate: float = 5e-5
    weight_decay: float = 0.0
    adam_beta1: float = 0.9
    adam_beta2: float = 0.999
    adam_epsilon: float = 1e-8
    max_grad_norm: float = 1.0
    num_train_epochs: float = 3.0
    max_steps: int = -1
    lr_scheduler_type: str = "linear"
    warmup_ratio: float = 0.0
    warmup_steps: int = 0
    log_level: str = "passive"
    log_level_replica: str = "warning"
    log_on_each_node: bool = True
    logging_dir: Optional[str] = None
    logging_strategy: str = "steps"
    logging_first_step: bool = False
    logging_steps: int = 500
    save_strategy: str = "steps"
    save_steps: int = 500
    save_total_limit: Optional[int] = None
    no_cuda: bool = False
    seed: int = 42
    fp16: bool = False
    fp16_opt_level: str = "O1"
    bf16: bool = False
    local_rank: int = -1
    xpu_backend: Optional[str] = None
    tpu_num_cores: Optional[int] = None
    tpu_metrics_debug: bool = False
    debug: bool = False
    dataloader_drop_last: bool = False
    eval_steps: int = 500
    dataloader_num_workers: int = 0
    past_index: int = -1
    run_name: Optional[str] = None
    disable_tqdm: bool = False
    remove_unused_columns: bool = True
    label_names: Optional[List[str]] = None
    load_best_model_at_end: bool = False
    metric_for_best_model: Optional[str] = None
    greater_is_better: Optional[bool] = None
    ignore_data_skip: bool = False
    sharded_ddp: List[str] = field(default_factory=list)
    deepspeed: Optional[str] = None
    label_smoothing_factor: float = 0.0
    adafactor: bool = False
    group_by_length: bool = False
    report_to: List[str] = field(default_factory=lambda: ["wandb"])
    ddp_find_unused_parameters: Optional[bool] = None
    ddp_bucket_cap_mb: Optional[int] = None
    dataloader_pin_memory: bool = True
    skip_memory_metrics: bool = True
    
    # Mixed precision training
    use_mixed_precision: bool = True
    mixed_precision_backend: str = "amp"  # "amp" or "deepspeed"
    
    # Distributed training
    distributed_training: bool = False
    world_size: int = 1
    local_world_size: int = 1
    distributed_backend: str = "nccl"  # "nccl" or "gloo"
    
    # Checkpointing
    checkpoint_dir: str = "./checkpoints"
    resume_from_checkpoint: Optional[str] = None
    save_optimizer: bool = True
    save_scheduler: bool = True
    
    # Evaluation and metrics
    eval_metrics: List[str] = field(default_factory=lambda: ["accuracy", "perplexity"])
    
    # Gradient accumulation and optimization
    gradient_checkpointing: bool = False
    
    def to_dict(self) -> Dict[str, Union[str, int, float, bool, List[str]]]:
        """Convert configuration to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith("_")
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Union[str, int, float, bool, List[str]]]) -> "TrainingConfig":
        """Create configuration from dictionary."""
        return cls(**config_dict)
    
    def save(self, config_file: str) -> None:
        """Save configuration to file."""
        import json
        import os
        
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, config_file: str) -> "TrainingConfig":
        """Load configuration from file."""
        import json
        
        with open(config_file, "r", encoding="utf-8") as f:
            config_dict = json.load(f)
        
        return cls.from_dict(config_dict)