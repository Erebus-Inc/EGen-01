"""Core implementation of the EGen-01 personal assistant."""

import logging
from typing import Dict, List, Optional, Union

from egen.model import THL150

logger = logging.getLogger(__name__)


class EGen01:
    """EGen-01 personal assistant main class.
    
    This class provides the core functionality for the EGen-01 personal assistant,
    including conversation management, tool usage, and personalization.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "cuda",
        precision: str = "fp16",
    ):
        """Initialize the EGen-01 assistant.
        
        Args:
            model_path: Path to the model checkpoint. If None, uses the default path.
            device: Device to run the model on ("cuda" or "cpu").
            precision: Model precision ("fp32", "fp16", "int8", or "int4").
        """
        self.model_path = model_path
        self.device = device
        self.precision = precision
        self.model = None
        self.conversation_history = []
        self.tools = {}
        self.user_preferences = {}
        
        logger.info(f"Initializing EGen-01 assistant with {precision} precision on {device}")
        
        # Load the model
        self._load_model()
        
    def _load_model(self):
        """Load the THL-150 model."""
        try:
            self.model = THL150.from_pretrained(
                self.model_path,
                device=self.device,
                precision=self.precision,
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def query(
        self, 
        text: str, 
        context: Optional[Dict] = None,
        use_tools: bool = True,
    ) -> Dict:
        """Process a user query and generate a response.
        
        Args:
            text: The user's query text.
            context: Additional context for the query.
            use_tools: Whether to allow the assistant to use tools.
            
        Returns:
            A dictionary containing the response and any additional information.
        """
        if self.model is None:
            logger.error("Model not loaded")
            return {"error": "Model not loaded"}
        
        # Add the query to the conversation history
        self.conversation_history.append({"role": "user", "content": text})
        
        # Process the query
        logger.info(f"Processing query: {text[:50]}...")
        
        # TODO: Implement actual query processing with the THL-150 model
        # For now, return a placeholder response
        response = {
            "text": f"I understand your query about '{text[:30]}...'. This is a placeholder response.",
            "tools_used": [],
            "confidence": 0.95,
        }
        
        # Add the response to the conversation history
        self.conversation_history.append({"role": "assistant", "content": response["text"]})
        
        return response
    
    def register_tool(self, name: str, tool_fn):
        """Register a tool for the assistant to use.
        
        Args:
            name: The name of the tool.
            tool_fn: The tool function.
        """
        self.tools[name] = tool_fn
        logger.info(f"Registered tool: {name}")
    
    def set_user_preference(self, key: str, value: any):
        """Set a user preference.
        
        Args:
            key: The preference key.
            value: The preference value.
        """
        self.user_preferences[key] = value
        logger.info(f"Set user preference: {key}={value}")
    
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("Cleared conversation history")