"""Main API module for the EGen platform."""

import logging
import os
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from egen.model import THL150
from egen.assistant.core import EGen01

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="EGen Platform API",
    description="API for the EGen Platform: Unified AI Ecosystem with THL-150 architecture",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize model (lazy loading)
model = None
assistant = None

# Define request/response models
class QueryRequest(BaseModel):
    text: str
    context: Optional[Dict] = None
    use_tools: bool = True

class QueryResponse(BaseModel):
    text: str
    tools_used: List[str] = []
    confidence: float

# Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the EGen Platform API"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Process a query using the EGen-01 assistant."""
    global assistant
    
    # Initialize assistant if not already initialized
    if assistant is None:
        try:
            logger.info("Initializing EGen-01 assistant")
            assistant = EGen01()
        except Exception as e:
            logger.error(f"Failed to initialize assistant: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize assistant",
            )
    
    # Process the query
    try:
        response = assistant.query(
            text=request.text,
            context=request.context,
            use_tools=request.use_tools,
        )
        return response
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}",
        )

@app.post("/model/generate")
async def generate(request: Dict):
    """Generate text using the THL-150 model directly."""
    global model
    
    # Initialize model if not already initialized
    if model is None:
        try:
            logger.info("Initializing THL-150 model")
            model = THL150.from_pretrained()
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize model",
            )
    
    # Generate text
    try:
        # TODO: Implement actual text generation with the THL-150 model
        # For now, return a placeholder response
        return {
            "generated_text": f"This is a placeholder response for: '{request.get('prompt', '')[:30]}...'",
        }
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating text: {str(e)}",
        )

# Error handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"},
    )

# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    host = os.environ.get("API_HOST", "0.0.0.0")
    port = int(os.environ.get("API_PORT", 8000))
    
    uvicorn.run("egen.api.main:app", host=host, port=port, reload=True)