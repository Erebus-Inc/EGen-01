"""Advanced tests for the THL-150 model."""

import pytest
import torch
import numpy as np

from egen.model import THL150, ModelConfig
from egen.model.layers import DomainRouter, TransformerLayer


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
        domain_routing=True,
        domain_types=["general", "code", "math", "security"],
        domain_layer_allocation={
            "general": [0, 1, 2, 3],
            "code": [0, 1, 2, 3],
            "math": [0, 1, 2, 3],
            "security": [0, 1, 2, 3],
        },
        conditional_execution=True,
        layer_activation_threshold=0.2,
    )


def test_domain_router_initialization(model_config):
    """Test that the domain router can be initialized."""
    router = DomainRouter(model_config)
    assert router is not None
    assert router.domain_types == model_config.domain_types
    assert router.domain_layer_allocation == model_config.domain_layer_allocation
    assert router.domain_classifier is not None
    assert router.domain_embeddings is not None
    assert router.domain_embeddings.shape == (len(model_config.domain_types), model_config.hidden_size)


def test_domain_router_forward(model_config):
    """Test the forward pass of the domain router."""
    router = DomainRouter(model_config)
    batch_size = 2
    seq_length = 10
    
    # Create random hidden states
    hidden_states = torch.randn(batch_size, seq_length, model_config.hidden_size)
    
    # Forward pass
    enhanced_hidden_states, domain_weights = router(hidden_states)
    
    # Check output shapes
    assert enhanced_hidden_states.shape == hidden_states.shape
    assert len(domain_weights) == len(model_config.domain_types)
    
    # Check domain weights
    for domain in model_config.domain_types:
        assert domain in domain_weights
        assert 0.0 <= domain_weights[domain] <= 1.0


def test_domain_router_layer_activation(model_config):
    """Test the layer activation logic of the domain router."""
    router = DomainRouter(model_config)
    
    # Test with high domain weights (should activate)
    domain_weights = {domain: 0.8 for domain in model_config.domain_types}
    for layer_idx in range(model_config.num_layers):
        assert router.should_activate_layer(layer_idx, domain_weights)
    
    # Test with low domain weights (should not activate)
    domain_weights = {domain: 0.1 for domain in model_config.domain_types}
    for layer_idx in range(model_config.num_layers):
        assert not router.should_activate_layer(layer_idx, domain_weights)
    
    # Test with mixed domain weights
    domain_weights = {domain: 0.1 for domain in model_config.domain_types}
    domain_weights["code"] = 0.9  # Only code domain is active
    
    for layer_idx in range(model_config.num_layers):
        # All layers are allocated to the code domain in our test config
        assert router.should_activate_layer(layer_idx, domain_weights)


def test_transformer_layer_initialization(model_config):
    """Test that the transformer layer can be initialized."""
    for layer_idx in range(model_config.num_layers):
        layer = TransformerLayer(model_config, layer_idx)
        assert layer is not None
        assert layer.layer_idx == layer_idx
        assert layer.attention is not None
        assert layer.mlp is not None
        assert layer.input_layernorm is not None
        assert layer.post_attention_layernorm is not None


def test_model_with_conditional_execution(model_config):
    """Test the model with conditional execution enabled."""
    model = THL150(model_config)
    batch_size = 2
    seq_length = 10
    
    # Create random input IDs
    input_ids = torch.randint(
        0, model_config.vocab_size, (batch_size, seq_length), dtype=torch.long
    )
    
    # Set model to eval mode to test conditional execution
    model.eval()
    
    # Forward pass
    outputs = model(input_ids)
    
    # Check output shape
    assert outputs.shape == (batch_size, seq_length, model_config.vocab_size)


def test_model_gradient_flow(model_config):
    """Test that gradients flow properly through the model."""
    model = THL150(model_config)
    batch_size = 2
    seq_length = 10
    
    # Create random input IDs and target
    input_ids = torch.randint(
        0, model_config.vocab_size, (batch_size, seq_length), dtype=torch.long
    )
    target = torch.randint(
        0, model_config.vocab_size, (batch_size, seq_length), dtype=torch.long
    )
    
    # Forward pass
    outputs = model(input_ids)
    
    # Calculate loss
    loss_fn = torch.nn.CrossEntropyLoss()
    loss = loss_fn(outputs.view(-1, model_config.vocab_size), target.view(-1))
    
    # Check that loss is a scalar
    assert loss.dim() == 0
    
    # Backward pass
    loss.backward()
    
    # Check that all parameters have gradients
    for name, param in model.named_parameters():
        if param.requires_grad:
            assert param.grad is not None, f"Parameter {name} has no gradient"
            # Check that gradients are not NaN or Inf
            assert not torch.isnan(param.grad).any(), f"Parameter {name} has NaN gradient"
            assert not torch.isinf(param.grad).any(), f"Parameter {name} has Inf gradient"


def test_model_with_attention_mask(model_config):
    """Test the model with attention mask."""
    model = THL150(model_config)
    batch_size = 2
    seq_length = 10
    
    # Create random input IDs
    input_ids = torch.randint(
        0, model_config.vocab_size, (batch_size, seq_length), dtype=torch.long
    )
    
    # Create attention mask (1 for tokens to attend to, 0 for tokens to ignore)
    attention_mask = torch.ones(batch_size, seq_length)
    attention_mask[:, seq_length // 2:] = 0  # Mask out second half of sequence
    
    # Forward pass
    outputs = model(input_ids, attention_mask=attention_mask)
    
    # Check output shape
    assert outputs.shape == (batch_size, seq_length, model_config.vocab_size)


def test_model_generation(model_config):
    """Test the model's text generation capability."""
    model = THL150(model_config)
    
    # Set model to eval mode
    model.eval()
    
    # Generate text
    prompt = "This is a test"
    max_length = 20
    
    output = model.generate(prompt, max_length=max_length)
    
    # Check that output is a string
    assert isinstance(output, str)
    # Check that output starts with the prompt
    assert output.startswith(prompt)


def test_model_error_handling(model_config):
    """Test the model's error handling."""
    model = THL150(model_config)
    
    # Test with invalid input shape
    with pytest.raises(ValueError):
        # 3D input instead of 2D
        invalid_input = torch.randint(
            0, model_config.vocab_size, (2, 3, 4), dtype=torch.long
        )
        model(invalid_input)
    
    # Test with input exceeding max position embeddings
    with pytest.raises(ValueError):
        # Sequence length > max_position_embeddings
        long_input = torch.randint(
            0, model_config.vocab_size, 
            (2, model_config.max_position_embeddings + 1), 
            dtype=torch.long
        )
        model(long_input)


def test_model_with_past_key_values(model_config):
    """Test the model with past key values for efficient generation."""
    model = THL150(model_config)
    batch_size = 2
    seq_length = 10
    
    # Create random input IDs
    input_ids = torch.randint(
        0, model_config.vocab_size, (batch_size, seq_length), dtype=torch.long
    )
    
    # First forward pass to get past key values
    outputs = model(input_ids, use_cache=True)
    past_key_values = outputs.past_key_values if hasattr(outputs, "past_key_values") else None
    
    # Check that past_key_values is not None if the model supports caching
    if model.config.use_cache:
        assert past_key_values is not None
        
        # Create next token input
        next_token = torch.randint(
            0, model_config.vocab_size, (batch_size, 1), dtype=torch.long
        )
        
        # Forward pass with past key values
        next_outputs = model(next_token, past_key_values=past_key_values, use_cache=True)
        
        # Check output shape
        assert next_outputs.shape == (batch_size, 1, model_config.vocab_size)