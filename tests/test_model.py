"""Tests for the THL-150 model."""

import pytest
import torch

from egen.model import THL150
from egen.model.config import ModelConfig


@pytest.fixture
def model_config():
    """Create a test model configuration."""
    return ModelConfig(
        hidden_size=128,
        num_layers=4,
        num_attention_heads=4,
        intermediate_size=512,
        max_position_embeddings=1024,
        vocab_size=32000,
    )


def test_model_initialization(model_config):
    """Test that the model can be initialized."""
    model = THL150(model_config)
    assert model is not None
    assert isinstance(model, THL150)


def test_model_forward_pass(model_config):
    """Test that the model can perform a forward pass."""
    model = THL150(model_config)
    batch_size = 2
    seq_length = 10
    
    # Create random input IDs
    input_ids = torch.randint(
        0, model_config.vocab_size, (batch_size, seq_length), dtype=torch.long
    )
    
    # Forward pass
    outputs = model(input_ids)
    
    # Check output shape
    assert outputs.shape == (batch_size, seq_length, model_config.vocab_size)


def test_model_save_load(model_config, tmp_path):
    """Test that the model can be saved and loaded."""
    model = THL150(model_config)
    
    # Save the model
    save_path = tmp_path / "model"
    model.save_pretrained(save_path)
    
    # Load the model
    loaded_model = THL150.from_pretrained(save_path)
    
    # Check that the loaded model has the same configuration
    assert loaded_model.config.hidden_size == model.config.hidden_size
    assert loaded_model.config.num_layers == model.config.num_layers
    assert loaded_model.config.num_heads == model.config.num_heads


def test_thl150_instantiation_and_forward():
    # Use a small config for fast test
    config = ModelConfig(
        num_layers=2,
        hidden_size=16,
        intermediate_size=32,
        num_attention_heads=2,
        num_key_value_heads=2,
        max_position_embeddings=16,
        vocab_size=32,
    )
    model = THL150(config)
    batch_size = 2
    seq_length = 4
    input_ids = torch.randint(0, config.vocab_size, (batch_size, seq_length))
    outputs = model(input_ids=input_ids)
    assert 'logits' in outputs
    assert outputs['logits'].shape == (batch_size, seq_length, config.vocab_size)