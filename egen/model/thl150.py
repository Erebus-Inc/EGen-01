"""THL-150 transformer model implementation."""

import os
from typing import Dict, List, Optional, Tuple, Union

import torch
import torch.nn as nn
import torch.nn.functional as F

from egen.model.config import ModelConfig
from egen.model.layers import TransformerLayer, DomainRouter


class THL150(nn.Module):
    """THL-150 transformer model with domain routing and conditional execution."""

    def __init__(self, config: Optional[ModelConfig] = None):
        super().__init__()
        self.config = config or ModelConfig()
        
        # Embeddings
        self.embed_tokens = nn.Embedding(self.config.vocab_size, self.config.hidden_size)
        
        # Domain router
        self.domain_router = DomainRouter(self.config) if self.config.domain_routing else None
        
        # Transformer layers
        self.layers = nn.ModuleList(
            [TransformerLayer(self.config, i) for i in range(self.config.num_layers)]
        )
        
        # Final layer norm
        self.norm = nn.LayerNorm(self.config.hidden_size, eps=self.config.layer_norm_epsilon)
        
        # Output projection
        self.lm_head = nn.Linear(self.config.hidden_size, self.config.vocab_size, bias=False)
        
        # Initialize weights
        self.apply(self._init_weights)
        
        # Tie weights if configured
        if self.config.tie_word_embeddings:
            self.lm_head.weight = self.embed_tokens.weight
    
    def _init_weights(self, module: nn.Module) -> None:
        """Initialize the weights."""
        if isinstance(module, nn.Linear):
            module.weight.data.normal_(mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.Embedding):
            module.weight.data.normal_(mean=0.0, std=self.config.initializer_range)
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)
    
    def get_input_embeddings(self) -> nn.Embedding:
        """Get the input embeddings module."""
        return self.embed_tokens
    
    def set_input_embeddings(self, value: nn.Embedding) -> None:
        """Set the input embeddings module."""
        self.embed_tokens = value
    
    def get_output_embeddings(self) -> nn.Linear:
        """Get the output embeddings module."""
        return self.lm_head
    
    def set_output_embeddings(self, new_embeddings: nn.Linear) -> None:
        """Set the output embeddings module."""
        self.lm_head = new_embeddings
    
    def forward(
        self,
        input_ids: Optional[torch.LongTensor] = None,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_values: Optional[List[Tuple[torch.Tensor, torch.Tensor]]] = None,
        inputs_embeds: Optional[torch.Tensor] = None,
        labels: Optional[torch.LongTensor] = None,
        use_cache: Optional[bool] = None,
        output_attentions: Optional[bool] = None,
        output_hidden_states: Optional[bool] = None,
        return_dict: Optional[bool] = None,
    ) -> Dict[str, torch.Tensor]:
        """Forward pass for the THL-150 model."""
        # Set defaults
        use_cache = use_cache if use_cache is not None else self.config.use_cache
        output_attentions = output_attentions if output_attentions is not None else False
        output_hidden_states = output_hidden_states if output_hidden_states is not None else False
        return_dict = return_dict if return_dict is not None else True
        
        # Check input
        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both input_ids and inputs_embeds")
        
        # Get sequence length and batch size
        if input_ids is not None:
            batch_size, seq_length = input_ids.shape
        else:
            batch_size, seq_length = inputs_embeds.shape[:2]
        
        # Past key values length
        past_key_values_length = 0
        if past_key_values is not None:
            past_key_values_length = past_key_values[0][0].shape[2]
        
        # Position IDs
        if position_ids is None:
            position_ids = torch.arange(
                past_key_values_length,
                seq_length + past_key_values_length,
                dtype=torch.long,
                device=input_ids.device if input_ids is not None else inputs_embeds.device,
            )
            position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)
        
        # Prepare attention mask
        if attention_mask is not None:
            # Create causal mask
            if past_key_values_length > 0:
                past_mask = attention_mask[:, :past_key_values_length]
                current_mask = attention_mask[:, past_key_values_length:]
                attention_mask = torch.cat([past_mask, current_mask], dim=1)
            
            # Extend attention mask for attention computation
            attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)  # [batch_size, 1, 1, seq_length]
            attention_mask = attention_mask.to(dtype=self.dtype)  # fp16 compatibility
            attention_mask = (1.0 - attention_mask) * torch.finfo(self.dtype).min
        
        # Get embeddings
        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)
        
        hidden_states = inputs_embeds
        
        # Initialize outputs
        all_hidden_states = () if output_hidden_states else None
        all_self_attns = () if output_attentions else None
        next_decoder_cache = () if use_cache else None
        
        # Apply domain routing if enabled
        domain_weights = None
        if self.domain_router is not None:
            hidden_states, domain_weights = self.domain_router(hidden_states)
        
        # Process through transformer layers
        for i, layer in enumerate(self.layers):
            # Determine if layer should be active
            is_active = True
            if domain_weights is not None:
                is_active = self.domain_router.should_activate_layer(i, domain_weights)
            
            # Add hidden states to output if requested
            if output_hidden_states:
                all_hidden_states += (hidden_states,)
            
            # Get past key value
            past_key_value = past_key_values[i] if past_key_values is not None else None
            
            # Layer forward pass
            layer_outputs = layer(
                hidden_states,
                attention_mask=attention_mask,
                position_ids=position_ids,
                past_key_value=past_key_value,
                output_attentions=output_attentions,
                use_cache=use_cache,
                is_active=is_active,
            )
            
            # Update hidden states
            if isinstance(layer_outputs, tuple):
                hidden_states = layer_outputs[0]
            else:
                hidden_states = layer_outputs
            
            # Add attention outputs if requested
            if output_attentions and len(layer_outputs) > 1 and layer_outputs[1] is not None:
                all_self_attns += (layer_outputs[1],)
            
            # Add cache if requested
            if use_cache and len(layer_outputs) > 2 and layer_outputs[2] is not None:
                next_decoder_cache += (layer_outputs[2],)
        
        # Final layer norm
        hidden_states = self.norm(hidden_states)
        
        # Add final hidden states to output if requested
        if output_hidden_states:
            all_hidden_states += (hidden_states,)
        
        # Get logits
        logits = self.lm_head(hidden_states)
        
        # Calculate loss if labels provided
        loss = None
        if labels is not None:
            # Shift so that tokens < n predict n
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            
            # Flatten the tokens
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(
                shift_logits.view(-1, self.config.vocab_size),
                shift_labels.view(-1),
            )
        
        # Prepare output
        output = {
            "loss": loss,
            "logits": logits,
            "hidden_states": all_hidden_states,
            "attentions": all_self_attns,
            "past_key_values": next_decoder_cache,
            "domain_weights": domain_weights,
        }
        
        # Remove None values
        return {k: v for k, v in output.items() if v is not None}
    
    def prepare_inputs_for_generation(
        self,
        input_ids: torch.LongTensor,
        past_key_values: Optional[List[Tuple[torch.Tensor, torch.Tensor]]] = None,
        attention_mask: Optional[torch.Tensor] = None,
        **kwargs,
    ) -> Dict[str, torch.Tensor]:
        """Prepare inputs for generation."""
        # Only keep the last token for generation
        if past_key_values is not None:
            input_ids = input_ids[:, -1:]
        
        # Prepare inputs
        inputs = {"input_ids": input_ids}
        
        # Add past key values if available
        if past_key_values is not None:
            inputs["past_key_values"] = past_key_values
        
        # Add attention mask if available
        if attention_mask is not None:
            inputs["attention_mask"] = attention_mask
        
        return inputs
    
    def generate(
        self,
        prompt: str,
        max_length: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs,
    ) -> str:
        """Generate text from a prompt."""
        # This is a placeholder for tokenization and generation
        # In a real implementation, this would use a tokenizer and proper generation logic
        return f"Generated response for: {prompt}"
    
    @classmethod
    def from_pretrained(cls, model_path: str) -> "THL150":
        """Load a pretrained model."""
        # Load config
        config = ModelConfig.from_pretrained(model_path)
        
        # Create model
        model = cls(config)
        
        # Load weights
        if os.path.isfile(os.path.join(model_path, "pytorch_model.bin")):
            state_dict = torch.load(
                os.path.join(model_path, "pytorch_model.bin"),
                map_location="cpu",
            )
            model.load_state_dict(state_dict)
        
        return model
    
    def save_pretrained(self, save_directory: str) -> None:
        """Save model to directory."""
        os.makedirs(save_directory, exist_ok=True)
        
        # Save config
        self.config.save_pretrained(save_directory)
        
        # Save model weights
        torch.save(
            self.state_dict(),
            os.path.join(save_directory, "pytorch_model.bin"),
        )
    
    def load_checkpoint(self, checkpoint_path: str) -> None:
        """Load model checkpoint."""
        state_dict = torch.load(checkpoint_path, map_location="cpu")
        self.load_state_dict(state_dict)
    
    @property
    def dtype(self) -> torch.dtype:
        """Get model dtype."""
        return next(self.parameters()).dtype