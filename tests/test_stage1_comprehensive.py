"""Comprehensive tests for Stage 1: Foundation & Core Architecture."""

import pytest
import torch
import tempfile
import os
from pathlib import Path

from egen.model import THL150, ModelConfig
from egen.training.trainer import Trainer
from egen.training.config import TrainingConfig
from torch.utils.data import Dataset


class SimpleDataset(Dataset):
    """Simple dataset for testing."""
    
    def __init__(self, vocab_size=1000, seq_length=32, num_samples=100):
        self.vocab_size = vocab_size
        self.seq_length = seq_length
        self.num_samples = num_samples
    
    def __len__(self):
        return self.num_samples
    
    def __getitem__(self, idx):
        return {
            'input_ids': torch.randint(0, self.vocab_size, (self.seq_length,)),
            'labels': torch.randint(0, self.vocab_size, (self.seq_length,)),
        }


class TestStage1Infrastructure:
    """Test Stage 1.1: Base Infrastructure Setup."""
    
    def test_project_structure(self):
        """Test that basic project structure exists."""
        required_dirs = [
            "egen",
            "egen/model",
            "egen/training", 
            "egen/self_healing",
            "egen/self_optimization",
            "egen/data_autonomy",
            "tests",
            "docs"
        ]
        
        for dir_path in required_dirs:
            assert os.path.exists(dir_path), f"Required directory {dir_path} not found"
    
    def test_docker_setup(self):
        """Test that Docker configuration exists."""
        docker_files = [
            "docker-compose.yml",
            "docker/Dockerfile.model",
            "docker/Dockerfile.ui"
        ]
        
        for file_path in docker_files:
            assert os.path.exists(file_path), f"Docker file {file_path} not found"
    
    def test_requirements_file(self):
        """Test that requirements.txt exists and is readable."""
        assert os.path.exists("requirements.txt"), "requirements.txt not found"
        
        with open("requirements.txt", "r") as f:
            content = f.read()
            assert "torch" in content, "PyTorch not in requirements"
            assert len(content.strip()) > 0, "Requirements file is empty"


class TestStage1ModelArchitecture:
    """Test Stage 1.2: Core Model Architecture."""
    
    @pytest.fixture
    def small_config(self):
        """Create a small model configuration for testing."""
        return ModelConfig(
            num_layers=4,
            hidden_size=128,
            intermediate_size=512,
            num_attention_heads=4,
            num_key_value_heads=4,
            max_position_embeddings=512,
            vocab_size=1000,
        )
    
    def test_model_initialization(self, small_config):
        """Test THL-150 model initialization."""
        model = THL150(small_config)
        assert model is not None
        assert isinstance(model, THL150)
        assert model.config.num_layers == 4
        assert model.config.hidden_size == 128
    
    def test_model_forward_pass(self, small_config):
        """Test model forward pass."""
        model = THL150(small_config)
        batch_size = 2
        seq_length = 16
        
        input_ids = torch.randint(0, small_config.vocab_size, (batch_size, seq_length))
        
        with torch.no_grad():
            outputs = model(input_ids=input_ids)
        
        assert 'logits' in outputs
        assert outputs['logits'].shape == (batch_size, seq_length, small_config.vocab_size)
    
    def test_domain_routing(self, small_config):
        """Test domain routing functionality."""
        # Enable domain routing
        small_config.domain_routing = True
        model = THL150(small_config)
        
        assert model.domain_router is not None
        
        batch_size = 2
        seq_length = 16
        input_ids = torch.randint(0, small_config.vocab_size, (batch_size, seq_length))
        
        with torch.no_grad():
            outputs = model(input_ids=input_ids)
        
        assert 'logits' in outputs
        assert outputs['logits'].shape == (batch_size, seq_length, small_config.vocab_size)
    
    def test_model_save_load(self, small_config):
        """Test model save and load functionality."""
        model = THL150(small_config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            save_path = Path(temp_dir) / "test_model"
            
            # Save model
            model.save_pretrained(save_path)
            
            # Check that files were created
            assert (save_path / "config.json").exists()
            assert (save_path / "pytorch_model.bin").exists()
            
            # Load model
            loaded_model = THL150.from_pretrained(save_path)
            
            # Verify configuration
            assert loaded_model.config.num_layers == small_config.num_layers
            assert loaded_model.config.hidden_size == small_config.hidden_size


class TestStage1TrainingInfrastructure:
    """Test Stage 1.3: Basic Training Infrastructure."""
    
    @pytest.fixture
    def training_setup(self):
        """Set up training components."""
        model_config = ModelConfig(
            num_layers=2,
            hidden_size=64,
            intermediate_size=256,
            num_attention_heads=2,
            num_key_value_heads=2,
            max_position_embeddings=128,
            vocab_size=500,
        )
        
        model = THL150(model_config)
        dataset = SimpleDataset(vocab_size=500, seq_length=32, num_samples=20)
        
        training_config = TrainingConfig(
            per_device_train_batch_size=4,
            num_train_epochs=1,
            learning_rate=1e-4,
            use_mixed_precision=False,  # Disable for testing
            fp16=False,
            no_cuda=True,  # Force CPU for testing
            distributed_training=False,
            dataloader_num_workers=0,
            eval_steps=5,
            save_steps=10,
            logging_steps=5,
        )
        
        return model, dataset, training_config
    
    def test_trainer_initialization(self, training_setup):
        """Test trainer initialization."""
        model, dataset, training_config = training_setup
        
        trainer = Trainer(
            model=model,
            train_dataset=dataset,
            config=training_config
        )
        
        assert trainer.model is not None
        assert trainer.train_dataset is not None
        assert trainer.config is not None
    
    def test_training_step(self, training_setup):
        """Test a single training step."""
        model, dataset, training_config = training_setup
        
        trainer = Trainer(
            model=model,
            train_dataset=dataset,
            config=training_config
        )
        
        # Run training for one epoch
        result = trainer.train()
        
        assert isinstance(result, dict)
        assert 'loss' in result or 'train_loss' in result
    
    def test_model_checkpointing(self, training_setup):
        """Test model checkpointing functionality."""
        model, dataset, training_config = training_setup
        
        with tempfile.TemporaryDirectory() as temp_dir:
            training_config.output_dir = temp_dir
            training_config.save_steps = 5
            
            trainer = Trainer(
                model=model,
                train_dataset=dataset,
                config=training_config
            )
            
            # Run training
            trainer.train()
            
            # Check that checkpoint was created
            checkpoint_dirs = [d for d in os.listdir(temp_dir) if d.startswith("checkpoint")]
            assert len(checkpoint_dirs) > 0, "No checkpoints were created"
    
    def test_evaluation_framework(self, training_setup):
        """Test basic evaluation framework."""
        model, dataset, training_config = training_setup
        
        # Use same dataset for eval (just for testing)
        eval_dataset = SimpleDataset(vocab_size=500, seq_length=32, num_samples=10)
        
        trainer = Trainer(
            model=model,
            train_dataset=dataset,
            eval_dataset=eval_dataset,
            config=training_config
        )
        
        # Run evaluation
        eval_result = trainer.evaluate()
        
        assert isinstance(eval_result, dict)
        assert 'eval_loss' in eval_result


class TestStage1Integration:
    """Test Stage 1 integration and overall functionality."""
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        # Create model
        config = ModelConfig(
            num_layers=2,
            hidden_size=32,
            intermediate_size=128,
            num_attention_heads=2,
            num_key_value_heads=2,
            max_position_embeddings=64,
            vocab_size=100,
        )
        
        model = THL150(config)
        
        # Create dataset
        dataset = SimpleDataset(vocab_size=100, seq_length=16, num_samples=8)
        
        # Create training config
        training_config = TrainingConfig(
            per_device_train_batch_size=2,
            num_train_epochs=1,
            learning_rate=1e-3,
            use_mixed_precision=False,
            fp16=False,
            no_cuda=True,
            distributed_training=False,
            dataloader_num_workers=0,
            eval_steps=2,
            save_steps=4,
            logging_steps=2,
        )
        
        # Train model
        with tempfile.TemporaryDirectory() as temp_dir:
            training_config.output_dir = temp_dir
            
            trainer = Trainer(
                model=model,
                train_dataset=dataset,
                config=training_config
            )
            
            # Run training
            result = trainer.train()
            assert isinstance(result, dict)
            
            # Save model
            save_path = Path(temp_dir) / "final_model"
            model.save_pretrained(save_path)
            
            # Load and test model
            loaded_model = THL150.from_pretrained(save_path)
            
            # Test inference
            input_ids = torch.randint(0, 100, (1, 8))
            with torch.no_grad():
                outputs = loaded_model(input_ids=input_ids)
            
            assert 'logits' in outputs
            assert outputs['logits'].shape == (1, 8, 100)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])