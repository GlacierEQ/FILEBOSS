"""
DeepSeek-Coder API Server

This script implements a FastAPI server that provides API endpoints for
code generation, completion, insertion, and chat functionalities using
the DeepSeek-Coder models.
"""
import os
import time
import uuid
import logging
from typing import List, Dict, Any, Optional, Union
import torch
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from transformers import AutoTokenizer, AutoModelForCausalLM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.environ.get("LOG_DIR", "./logs"), "api.log"))
    ]
)
logger = logging.getLogger("DeepSeek-API")

# Initialize FastAPI app
app = FastAPI(
    title="DeepSeek-Coder API",
    description="API for code generation, completion, and chat using DeepSeek-Coder models",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security - API key header
API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)

# Model configurations
MODEL_CONFIGS = {
    "base": {
        "model_id": "deepseek-ai/deepseek-coder-6.7b-base",
        "use_flash_attention": True,
    },
    "large": {
        "model_id": "deepseek-ai/deepseek-coder-33b-instruct",
        "use_flash_attention": True,
    },
}

# Global variables for loaded models
tokenizer = None
model = None
model_name = None
device = "cuda" if torch.cuda.is_available() else "cpu"

# Environment variables
MODEL_SIZE = os.environ.get("MODEL_SIZE", "base")
API_KEYS = os.environ.get("API_KEYS", "").split(",")
ENABLE_AUTH = os.environ.get("ENABLE_AUTH", "false").lower() == "true"
MAX_REQUEST_TOKENS = int(os.environ.get("MAX_REQUEST_TOKENS", "4096"))

# Request rate limiting
request_counts = {}
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "100"))  # requests per hour
RATE_WINDOW = 3600  # 1 hour in seconds

# Pydantic models for request/response
class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = Field(default=100, ge=1, le=2048)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    language: Optional[str] = None
    stop: Optional[List[str]] = None

class InsertionRequest(BaseModel):
    prefix: str
    suffix: str
    max_tokens: int = Field(default=100, ge=1, le=2048)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    stop: Optional[List[str]] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: int = Field(default=500, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    stop: Optional[List[str]] = None

# Helper functions
def verify_api_key(api_key: Optional[str] = Depends(API_KEY_HEADER)):
    """Verify the API key."""
    if not ENABLE_AUTH:
        return True
    
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
        
    # Extract token from "Bearer {token}"
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
        
    if api_key not in API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    # Check rate limit
    current_time = time.time()
    if api_key in request_counts:
        count, window_start = request_counts[api_key]
        # If the window has expired, reset the count
        if current_time - window_start > RATE_WINDOW:
            request_counts[api_key] = (1, current_time)
        else:
            # Check if rate limit is exceeded
            if count >= RATE_LIMIT:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {RATE_LIMIT} requests per hour.",
                )
            # Increment count
            request_counts[api_key] = (count + 1, window_start)
    else:
        request_counts[api_key] = (1, current_time)
    
    return True

def load_model():
    """Load the model and tokenizer based on environment configuration."""
    global tokenizer, model, model_name
    
    if model is not None:
        return
    
    try:
        config = MODEL_CONFIGS.get(MODEL_SIZE, MODEL_CONFIGS["base"])
        model_id = config["model_id"]
        use_flash_attention = config.get("use_flash_attention", False)
        
        logger.info(f"Loading tokenizer: {model_id}")
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        
        logger.info(f"Loading model: {model_id}")
        torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        
        model_kwargs = {
            "trust_remote_code": True,
            "torch_dtype": torch_dtype,
        }
        
        if use_flash_attention and torch.cuda.is_available():
            model_kwargs["attn_implementation"] = "flash_attention_2"
        
        model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
        
        if torch.cuda.is_available():
            model = model.cuda()
        
        model_name = model_id.split("/")[-1]
        logger.info(f"Model {model_name} loaded successfully.")
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise

def count_tokens(text: str) -> int:
    """Count the number of tokens in the text."""
    if tokenizer is None:
        load_model()
    return len(tokenizer.encode(text))

async def check_request_size(request: Request):
    """Check if the request body is too large."""
    body = await request.body()
    if len(body) > MAX_REQUEST_TOKENS * 8:  # Approximate byte size limit
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Request body too large",
        )

# API endpoints
@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    load_model()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "model": model_name}

@app.post("/api/v1/completion", dependencies=[Depends(verify_api_key)])
async def completion(request: CompletionRequest):
    """
    Generate code completion based on the provided prompt.
    """
    try:
        # Check token count
        token_count = count_tokens(request.prompt)
        if token_count > MAX_REQUEST_TOKENS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Prompt too long. Contains {token_count} tokens, maximum is {MAX_REQUEST_TOKENS}."
            )
        
        # Prepare inputs
        inputs = tokenizer(request.prompt, return_tensors="pt").to(device)
        
        # Generate completion
        stop_tokens = request.stop if request.stop else []
        if isinstance(stop_tokens, str):
            stop_tokens = [stop_tokens]
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=request.temperature > 0.0,
            )
        
        # Decode the generated text
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        completion_text = generated_text[len(request.prompt):]
        
        # Apply stop tokens
        for stop_token in stop_tokens:
            if stop_token in completion_text:
                completion_text = completion_text[:completion_text.index(stop_token)]
        
        # Calculate token counts
        prompt_tokens = count_tokens(request.prompt)
        completion_tokens = count_tokens(completion_text)
        
        # Build response
        response = {
            "id": f"cmpl-{str(uuid.uuid4())[:8]}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": model_name,
            "choices": [
                {
                    "text": completion_text,
                    "index": 0,
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
        }
        
        return response
    
    except Exception as e:
        logger.error(f"Error in completion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during code completion: {str(e)}"
        )

@app.post("/api/v1/insertion", dependencies=[Depends(verify_api_key)])
async def insertion(request: InsertionRequest):
    """
    Generate code to insert between prefix and suffix.
    """
    try:
        # Check token count
        combined_text = f"{request.prefix}<｜fim▁hole｜>{request.suffix}"
        token_count = count_tokens(combined_text)
        if token_count > MAX_REQUEST_TOKENS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input too long. Contains {token_count} tokens, maximum is {MAX_REQUEST_TOKENS}."
            )
        
        # Prepare inputs for fill-in-middle task
        fim_text = f"<｜fim▁begin｜>{request.prefix}<｜fim▁hole｜>{request.suffix}<｜fim▁end｜>"
        inputs = tokenizer(fim_text, return_tensors="pt").to(device)
        
        # Generate insertion
        stop_tokens = request.stop if request.stop else []
        if isinstance(stop_tokens, str):
            stop_tokens = [stop_tokens]
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=request.temperature > 0.0,
            )
        
        # Decode the generated text
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract the insertion part
        insertion_text = generated_text[len(fim_text):]
        
        # Apply stop tokens
        for stop_token in stop_tokens:
            if stop_token in insertion_text:
                insertion_text = insertion_text[:insertion_text.index(stop_token)]
        
        # Calculate token counts
        prompt_tokens = token_count
        insertion_tokens = count_tokens(insertion_text)
        
        # Build response
        response = {
            "id": f"ins-{str(uuid.uuid4())[:8]}",
            "object": "text_insertion",
            "created": int(time.time()),
            "model": model_name,
            "choices": [
                {
                    "text": insertion_text,
                    "index": 0,
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": insertion_tokens,
                "total_tokens": prompt_tokens + insertion_tokens
            }
        }
        
        return response
    
    except Exception as e:
        logger.error(f"Error in insertion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during code insertion: {str(e)}"
        )

@app.post("/api/v1/chat", dependencies=[Depends(verify_api_key)])
async def chat(request: ChatRequest):
    """
    Generate chat completion based on the provided messages.
    """
    try:
        # Check token count
        messages_text = "\n".join([f"{m.role}: {m.content}" for m in request.messages])
        token_count = count_tokens(messages_text)
        if token_count > MAX_REQUEST_TOKENS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Messages too long. Contains {token_count} tokens, maximum is {MAX_REQUEST_TOKENS}."
            )
        
        # Convert messages to the format expected by the model
        chat_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Prepare inputs
        inputs = tokenizer.apply_chat_template(
            chat_messages, 
            add_generation_prompt=True, 
            return_tensors="pt"
        ).to(device)
        
        # Generate chat completion
        stop_tokens = request.stop if request.stop else []
        if isinstance(stop_tokens, str):
            stop_tokens = [stop_tokens]
        
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=request.temperature > 0.0,
                eos_token_id=tokenizer.eos_token_id,
            )
        
        # Decode the generated text
        generated_text = tokenizer.decode(outputs[0][len(inputs[0]):], skip_special_tokens=True)
        
        # Apply stop tokens
        for stop_token in stop_tokens:
            if stop_token in generated_text:
                generated_text = generated_text[:generated_text.index(stop_token)]
        
        # Calculate token counts
        prompt_tokens = token_count
        completion_tokens = count_tokens(generated_text)
        
        # Build response
        response = {
            "id": f"chat-{str(uuid.uuid4())[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": generated_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
        }
        
        return response
    
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during chat completion: {str(e)}"
        )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all API requests."""
    start_time = time.time()
    
    # Check request size
    await check_request_size(request)
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Start the server
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=port,
        log_level=os.environ.get("LOG_LEVEL", "info").lower(),
        reload=False
    )
