"""Transformer layers for the THL-150 model."""

import math
from typing import Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn
import torch.nn.functional as F

from egen.model.config import ModelConfig


class RotaryEmbedding(nn.Module):
    """Rotary position embeddings for transformer models."""

    def __init__(self, dim: int, max_position_embeddings: int = 32768, base: int = 10000):
        super().__init__()
        self.dim = dim
        self.max_position_embeddings = max_position_embeddings
        self.base = base
        
        # Create rotary position embedding cache
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq, persistent=False)
        self._set_cos_sin_cache(
            seq_len=max_position_embeddings, device=self.inv_freq.device, dtype=self.inv_freq.dtype
        )

    def _set_cos_sin_cache(self, seq_len: int, device: torch.device, dtype: torch.dtype) -> None:
        """Set up the cache for cos and sin values."""
        self.max_seq_len_cached = seq_len
        t = torch.arange(seq_len, device=device, dtype=dtype)
        
        # Compute cos and sin values
        freqs = torch.einsum("i,j->ij", t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        
        self.register_buffer("cos_cached", emb.cos()[None, None, :, :], persistent=False)
        self.register_buffer("sin_cached", emb.sin()[None, None, :, :], persistent=False)

    def forward(self, x: torch.Tensor, seq_len: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get the cos and sin embeddings for the given sequence length."""
        # Reset the cache if needed
        if seq_len > self.max_seq_len_cached:
            self._set_cos_sin_cache(seq_len, device=x.device, dtype=x.dtype)

        return (
            self.cos_cached[:, :, :seq_len, ...].to(dtype=x.dtype),
            self.sin_cached[:, :, :seq_len, ...].to(dtype=x.dtype),
        )


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    """Rotate half of the hidden dimensions of the input."""
    x1, x2 = x.chunk(2, dim=-1)
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_pos_emb(q: torch.Tensor, k: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """Apply rotary position embeddings to query and key tensors."""
    # Reshape for broadcasting
    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed


class DomainRouter(nn.Module):
    """Domain routing module for specialized attention."""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.domain_types = config.domain_types
        self.domain_layer_allocation = config.domain_layer_allocation
        
        # Domain classifier
        self.domain_classifier = nn.Linear(config.hidden_size, len(config.domain_types))
        
        # Domain embeddings
        self.domain_embeddings = nn.Parameter(
            torch.randn(len(config.domain_types), config.hidden_size)
        )

    def forward(self, hidden_states: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, float]]:
        """Classify input into domains and return domain weights."""
        # Average pooling over sequence length
        pooled_output = hidden_states.mean(dim=1)
        
        # Classify domains
        domain_logits = self.domain_classifier(pooled_output)
        domain_weights = F.softmax(domain_logits, dim=-1)
        
        # Create domain weights dictionary
        domain_weights_dict = {}
        for i, domain in enumerate(self.domain_types):
            domain_weights_dict[domain] = domain_weights[:, i].mean().item()
        
        # Apply domain embeddings
        domain_embedding = torch.matmul(domain_weights, self.domain_embeddings)
        domain_embedding = domain_embedding.unsqueeze(1).expand(-1, hidden_states.size(1), -1)
        
        # Add domain embedding to hidden states
        enhanced_hidden_states = hidden_states + domain_embedding
        
        return enhanced_hidden_states, domain_weights_dict

    def should_activate_layer(self, layer_idx: int, domain_weights: Dict[str, float]) -> bool:
        """Determine if a layer should be activated based on domain weights."""
        if not self.config.conditional_execution:
            return True
        
        # Check if layer belongs to any active domain
        for domain, weight in domain_weights.items():
            if layer_idx in self.domain_layer_allocation.get(domain, []) and \
               weight >= self.config.layer_activation_threshold:
                return True
        
        return False


class AttentionModule(nn.Module):
    """Multi-head attention module with support for domain routing."""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.hidden_size = config.hidden_size
        self.num_heads = config.num_attention_heads
        self.head_dim = self.hidden_size // self.num_heads
        self.num_key_value_heads = config.num_key_value_heads
        self.num_key_value_groups = self.num_heads // self.num_key_value_heads
        
        # Check if dimensions are compatible
        if self.head_dim * self.num_heads != self.hidden_size:
            raise ValueError(
                f"hidden_size {self.hidden_size} is not divisible by num_heads {self.num_heads}"
            )
        
        # Query, key, value projections
        self.q_proj = nn.Linear(self.hidden_size, self.num_heads * self.head_dim, bias=config.attention_bias)
        self.k_proj = nn.Linear(self.hidden_size, self.num_key_value_heads * self.head_dim, bias=config.attention_bias)
        self.v_proj = nn.Linear(self.hidden_size, self.num_key_value_heads * self.head_dim, bias=config.attention_bias)
        self.o_proj = nn.Linear(self.num_heads * self.head_dim, self.hidden_size, bias=config.attention_bias)
        
        # Rotary embeddings
        self.rotary_emb = RotaryEmbedding(
            self.head_dim,
            max_position_embeddings=config.max_position_embeddings,
            base=config.rope_theta,
        )

    def _shape(self, tensor: torch.Tensor, seq_len: int, bsz: int) -> torch.Tensor:
        """Reshape tensor for attention computation."""
        return tensor.view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        output_attentions: bool = False,
        use_cache: bool = False,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor], Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        """Forward pass for attention module."""
        bsz, q_len, _ = hidden_states.size()

        # Project query, key, value
        query_states = self.q_proj(hidden_states)
        key_states = self.k_proj(hidden_states)
        value_states = self.v_proj(hidden_states)

        # Reshape
        query_states = self._shape(query_states, q_len, bsz)
        key_states = self._shape(key_states, q_len, bsz)
        value_states = self._shape(value_states, q_len, bsz)

        # Handle past key values
        kv_seq_len = q_len
        if past_key_value is not None:
            kv_seq_len += past_key_value[0].shape[-2]
            key_states = torch.cat([past_key_value[0], key_states], dim=2)
            value_states = torch.cat([past_key_value[1], value_states], dim=2)

        # Update cache
        past_key_value = (key_states, value_states) if use_cache else None

        # Apply rotary embeddings
        if position_ids is None:
            position_ids = torch.arange(q_len, device=hidden_states.device).unsqueeze(0)
        cos, sin = self.rotary_emb(value_states, seq_len=kv_seq_len)
        query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)

        # Compute attention
        # Flash attention if available
        if hasattr(F, "scaled_dot_product_attention") and self.config.use_flash_attention:
            # Transpose to [batch_size, num_heads, seq_len, head_dim]
            attn_output = F.scaled_dot_product_attention(
                query_states, key_states, value_states, attn_mask=attention_mask
            )
            attention_probs = None  # Flash attention doesn't return attention probs
        else:
            # Traditional attention
            attn_weights = torch.matmul(query_states, key_states.transpose(2, 3)) / math.sqrt(self.head_dim)
            
            # Apply attention mask
            if attention_mask is not None:
                attn_weights = attn_weights + attention_mask
            
            # Softmax
            attn_weights = F.softmax(attn_weights, dim=-1, dtype=torch.float32).to(query_states.dtype)
            
            # Get attention output
            attn_output = torch.matmul(attn_weights, value_states)
            attention_probs = attn_weights if output_attentions else None

        # Reshape output
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.reshape(bsz, q_len, self.hidden_size)

        # Output projection
        attn_output = self.o_proj(attn_output)

        return attn_output, attention_probs, past_key_value


class MLP(nn.Module):
    """MLP module for transformer layers."""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.hidden_size = config.hidden_size
        self.intermediate_size = config.intermediate_size
        
        self.gate_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=False)
        self.up_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=False)
        self.down_proj = nn.Linear(self.intermediate_size, self.hidden_size, bias=False)
        self.act_fn = F.silu

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass for MLP module."""
        # SwiGLU activation
        gate = self.act_fn(self.gate_proj(x))
        up = self.up_proj(x)
        intermediate = gate * up
        
        # Down projection
        output = self.down_proj(intermediate)
        return output


class TransformerLayer(nn.Module):
    """Transformer layer for the THL-150 model."""

    def __init__(self, config: ModelConfig, layer_idx: int):
        super().__init__()
        self.config = config
        self.layer_idx = layer_idx
        self.hidden_size = config.hidden_size
        
        # Layer components
        self.input_layernorm = nn.LayerNorm(self.hidden_size, eps=config.layer_norm_epsilon)
        self.self_attn = AttentionModule(config)
        self.post_attention_layernorm = nn.LayerNorm(self.hidden_size, eps=config.layer_norm_epsilon)
        self.mlp = MLP(config)

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        output_attentions: bool = False,
        use_cache: bool = False,
        is_active: bool = True,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor], Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        """Forward pass for transformer layer."""
        # Skip layer if not active (conditional execution)
        if not is_active:
            return hidden_states, None, past_key_value
        
        # Attention block
        residual = hidden_states
        hidden_states = self.input_layernorm(hidden_states)
        
        # Self attention
        hidden_states, self_attn_weights, present_key_value = self.self_attn(
            hidden_states=hidden_states,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_value=past_key_value,
            output_attentions=output_attentions,
            use_cache=use_cache,
        )
        
        # Residual connection
        hidden_states = residual + hidden_states
        
        # MLP block
        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        
        # Residual connection
        hidden_states = residual + hidden_states
        
        outputs = (hidden_states,)
        
        if output_attentions:
            outputs += (self_attn_weights,)
        
        if use_cache:
            outputs += (present_key_value,)
        
        return outputs