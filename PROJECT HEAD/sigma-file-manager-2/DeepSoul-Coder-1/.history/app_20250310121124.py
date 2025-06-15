#!/usr/bin/env python3
"""
DeepSeek-Coder API Server

Main entry point for the DeepSeek-Coder API service providing code generation, 
completion, and chat capabilities.
"""

import os
import gc
import time
import json
import logging
import torch
import uuid
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager
from datetime import datetime

# FastAPI imports
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator

# Import monitoring
try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server
    ENABLE_METRICS = os.environ.get("ENABLE_METRICS", "true").lower() == "true"
except ImportError:
    ENABLE_METRICS = False
    print("prometheus_client not installed. Metrics disabled.")

# Import model utilities
from utils.model_loader import load_model_and_tokenizer
from utils.auth import verify_api_key
from utils.rate_limiter import RateLimiter
from utils.memory_manager import MemoryManager

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.environ.get("LOG_DIR", "logs"), "api_server.log"))
    ]
)
logger = logging.getLogger("deepseek-coder")

# Global variables for model and tokenizer
model = None
tokenizer = None
memory_manager = None

# Configuration
MODEL_SIZE = os.environ.get("MODEL_SIZE", "base")
MODEL_PATH = os.path.join(os.environ.get("MODEL_PATH", "models"), MODEL_SIZE)
ENABLE_AUTH = os.environ.get("ENABLE_AUTH", "false").lower() == "true"
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "100"))  # requests per hour
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DEFAULT_MAX_TOKENS = 500
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.95
MAX_INPUT_TOKENS = 4096

# Setup rate limiter
rate_limiter = RateLimiter(limit=RATE_LIMIT, window=3600)  # 1 hour window

# Prometheus metrics (if enabled)
if ENABLE_METRICS:
    REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status'])
    REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])
    TOKEN_COUNT = Counter('generated_tokens_total', 'Total Generated Tokens')
    PROMPT_TOKEN_COUNT = Counter('prompt_tokens_total', 'Total Prompt Tokens')
    MODEL_MEMORY_USAGE = Gauge('model_memory_usage_bytes', 'Model Memory Usage')
    CUDA_MEMORY_USAGE = Gauge('cuda_memory_usage_bytes', 'CUDA Memory Usage')
    QUEUE_SIZE = Gauge('request_queue_size', 'Request Queue Size')

# Setup security
security = HTTPBearer(auto_error=False)

# ===== Pydantic Models =====

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = Field(default=DEFAULT_MAX_TOKENS)
    temperature: float = Field(default=DEFAULT_TEMPERATURE, ge=0.0, le=2.0)
    top_p: float = Field(default=DEFAULT_TOP_P, ge=0.0, le=1.0)
    language: Optional[str] = None
    stop: Optional[Union[List[str], str]] = None
    
    @validator('max_tokens')
    def max_tokens_range(cls, v):
        if v < 1 or v > 2048:
            raise ValueError('max_tokens must be between 1 and 2048')
        return v

class InsertionRequest(BaseModel):
    prefix: str
    suffix: str
    max_tokens: int = Field(default=DEFAULT_MAX_TOKENS)
    temperature: float = Field(default=DEFAULT_TEMPERATURE, ge=0.0, le=2.0)
    top_p: float = Field(default=DEFAULT_TOP_P, ge=0.0, le=1.0)
    stop: Optional[Union[List[str], str]] = None
    
    @validator('max_tokens')
    def max_tokens_range(cls, v):
        if v < 1 or v > 2048:
            raise ValueError('max_tokens must be between 1 and 2048')
        return v

class ChatMessage(BaseModel):
    role: str
    content: str
    
    @validator('role')
    def valid_role(cls, v):
        if v not in ['system', 'user', 'assistant']:
            raise ValueError('role must be one of: system, user, assistant')
        return v

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: int = Field(default=DEFAULT_MAX_TOKENS)
    temperature: float = Field(default=DEFAULT_TEMPERATURE, ge=0.0, le=2.0)
    top_p: float = Field(default=DEFAULT_TOP_P, ge=0.0, le=1.0)
    stop: Optional[Union[List[str], str]] = None
    
    @validator('max_tokens')
    def max_tokens_range(cls, v):
        if v < 1 or v > 4096:
            raise ValueError('max_tokens must be between 1 and 4096')
        return v
    
    @validator('messages')
    def messages_not_empty(cls, v):
        if not v:
            raise ValueError('messages cannot be empty')
        return v

# ===== Application Startup and Shutdown =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model and tokenizer on startup
    global model, tokenizer, memory_manager
    model, tokenizer = load_model_and_tokenizer(MODEL_PATH, device=DEVICE)
    memory_manager = MemoryManager(interval_seconds=60, target_usage=0.8)
    memory_manager.start()
    
    # Start Prometheus metrics server if enabled
    if ENABLE_METRICS:
        prometheus_port = int(os.environ.get("PROMETHEUS_PORT", 9090))
        start_http_server(prometheus_port)
        logger.info(f"Prometheus metrics server started on port {prometheus_port}")
    
    logger.info(f"DeepSeek-Coder API server initialized with model: {MODEL_PATH}")
    logger.info(f"Running on device: {DEVICE}")
    logger.info(f"Authentication enabled: {ENABLE_AUTH}")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down server...")
    memory_manager.stop()
    
    # Clear CUDA cache and delete model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    del model
    del tokenizer
    gc.collect()
    logger.info("Server shutdown complete.")

# Initialize FastAPI application
app = FastAPI(
    title="DeepSeek-Coder API",
    description="API for DeepSeek-Coder, an advanced AI code assistant.",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOW_ORIGINS", "*").split(","),
    allow_credentials=os.environ.get("ALLOW_CREDENTIALS", "false").lower() == "true",
    allow_methods=os.environ.get("ALLOW_METHODS", "GET,POST,OPTIONS").split(","),
    allow_headers=os.environ.get("ALLOW_HEADERS", "Content-Type,Authorization").split(","),
)

# ===== Authentication Middleware =====

async def get_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    if ENABLE_AUTH:
        if credentials is None or not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        api_key = credentials.credentials
        if not verify_api_key(api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Apply rate limiting
        if not rate_limiter.allow_request(api_key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
        
        return api_key
    return None

# ===== Request/Response Logging Middleware =====

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Generate a request ID for tracking
    request_id = str(uuid.uuid4())
    
    # Log request details
    logger.debug(f"Request {request_id} started: {request.method} {request.url.path}")
    
    # Process the request
    try:
        response = await call_next(request)
        
        # Calculate latency
        latency = time.time() - start_time
        
        # Record metrics if enabled
        if ENABLE_METRICS:
            REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
            REQUEST_LATENCY.labels(request.method, request.url.path).observe(latency)
            
            # Update memory metrics
            if DEVICE == "cuda" and torch.cuda.is_available():
                CUDA_MEMORY_USAGE.set(torch.cuda.memory_allocated())
                
            if model is not None:
                # Estimate model memory usage
                model_size_bytes = sum(p.numel() * p.element_size() for p in model.parameters())
                MODEL_MEMORY_USAGE.set(model_size_bytes)
        
        # Log response details
        logger.debug(f"Request {request_id} completed: {response.status_code} in {latency:.3f}s")
        
        return response
        
    except Exception as e:
        # Log exception
        logger.error(f"Request {request_id} failed: {str(e)}")
        raise

# ===== Routes =====

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "model": MODEL_PATH}

@app.post("/api/v1/completion")
async def completion(
    request: CompletionRequest,
    background_tasks: BackgroundTasks,
    api_key: Optional[str] = Depends(get_api_key)
):
    """Generate code completion."""
    try:
        if model is None or tokenizer is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Prepare inputs
        inputs = tokenizer(request.prompt, return_tensors="pt")
        input_ids = inputs.input_ids.to(DEVICE)
        
        # Check token length
        if input_ids.shape[1] > MAX_INPUT_TOKENS:
            raise HTTPException(status_code=400, detail="Input too long")
            
        # Prepare stop sequences
        stop_sequences = []
        if request.stop:
            if isinstance(request.stop, str):
                stop_sequences = [request.stop]
            else:
                stop_sequences = request.stop
        
        # Generate completion
        with torch.no_grad():
            outputs = model.generate(
                input_ids,
                max_length=input_ids.shape[1] + request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=request.temperature > 0,
                pad_token_id=tokenizer.eos_token_id,
            )
        
        # Decode and clean up output
        prompt_length = len(tokenizer.decode(input_ids[0], skip_special_tokens=True))
        completion_text = tokenizer.decode(outputs[0], skip_special_tokens=True)[prompt_length:]
        
        # Apply stop sequences
        for stop_seq in stop_sequences:
            if stop_seq in completion_text:
                completion_text = completion_text[:completion_text.index(stop_seq)]
        
        # Calculate token counts
        prompt_tokens = input_ids.shape[1]
        completion_tokens = outputs.shape[1] - input_ids.shape[1]
        
        # Update metrics
        if ENABLE_METRICS:
            PROMPT_TOKEN_COUNT.inc(prompt_tokens)
            TOKEN_COUNT.inc(completion_tokens)
        
        # Schedule memory cleanup for large models
        background_tasks.add_task(memory_manager.check_memory)
        
        # Return response
        response = {
            "id": f"cmpl-{str(uuid.uuid4())[:8]}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": MODEL_PATH,
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
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Error generating completion: {str(e)}")

@app.post("/api/v1/insertion")
async def insertion(
    request: InsertionRequest,
    background_tasks: BackgroundTasks,
    api_key: Optional[str] = Depends(get_api_key)
):
    """Generate code insertion between prefix and suffix."""
    try:
        if model is None or tokenizer is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Prepare the combined prompt for insertion
        # For insertion task, we use a special format: prefix + <insertion_point> + suffix
        # The model will generate text to replace the <insertion_point> token
        combined_prompt = f"{request.prefix}\n<insertion_point>\n{request.suffix}"
        
        # Tokenize inputs
        inputs = tokenizer(combined_prompt, return_tensors="pt")
        input_ids = inputs.input_ids.to(DEVICE)
        
        # Check token length
        if input_ids.shape[1] > MAX_INPUT_TOKENS:
            raise HTTPException(status_code=400, detail="Input too long")
            
        # Prepare stop sequences
        stop_sequences = []
        if request.stop:
            if isinstance(request.stop, str):
                stop_sequences = [request.stop]
            else:
                stop_sequences = request.stop
        
        # Generate completion
        with torch.no_grad():
            outputs = model.generate(
                input_ids,
                max_length=input_ids.shape[1] + request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=request.temperature > 0,
                pad_token_id=tokenizer.eos_token_id,
            )
        
        # Decode output and extract insertion
        full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract the insertion between prefix and suffix
        prefix = request.prefix
        suffix = request.suffix
        
        if prefix in full_output and suffix in full_output:
            # Find the insertion between prefix and suffix
            prefix_end = full_output.find(prefix) + len(prefix)
            suffix_start = full_output.find(suffix, prefix_end)
            insertion_text = full_output[prefix_end:suffix_start].strip()
        else:
            # Fallback: extract any new content
            decoded_input = tokenizer.decode(input_ids[0], skip_special_tokens=True)
            insertion_text = full_output[len(decoded_input):].strip()
        
        # Apply stop sequences
        for stop_seq in stop_sequences:
            if stop_seq in insertion_text:
                insertion_text = insertion_text[:insertion_text.index(stop_seq)]
        
        # Calculate token counts
        prompt_tokens = input_ids.shape[1]
        completion_tokens = outputs.shape[1] - input_ids.shape[1]
        
        # Update metrics
        if ENABLE_METRICS:
            PROMPT_TOKEN_COUNT.inc(prompt_tokens)
            TOKEN_COUNT.inc(completion_tokens)
        
        # Schedule memory cleanup for large models
        background_tasks.add_task(memory_manager.check_memory)
        
        # Return response
        response = {
            "id": f"ins-{str(uuid.uuid4())[:8]}",
            "object": "text_insertion",
            "created": int(time.time()),
            "model": MODEL_PATH,
            "choices": [
                {
                    "text": insertion_text,
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
        logger.error(f"Error in insertion: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Error generating insertion: {str(e)}")

@app.post("/api/v1/chat")
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    api_key: Optional[str] = Depends(get_api_key)
):
    """Chat with the AI model."""
    try:
        if model is None or tokenizer is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Format messages for the model
        formatted_prompt = ""
        for msg in request.messages:
            if msg.role == "system":
                formatted_prompt += f"<|system|>\n{msg.content}\n"
            elif msg.role == "user":
                formatted_prompt += f"<|user|>\n{msg.content}\n"
            elif msg.role == "assistant":
                formatted_prompt += f"<|assistant|>\n{msg.content}\n"
        
        # Add the final assistant prompt
        formatted_prompt += "<|assistant|>\n"
        
        # Tokenize inputs
        inputs = tokenizer(formatted_prompt, return_tensors="pt")
        input_ids = inputs.input_ids.to(DEVICE)
        
        # Check token length
        if input_ids.shape[1] > MAX_INPUT_TOKENS:
            raise HTTPException(status_code=400, detail="Input too long")
            
        # Prepare stop sequences
        stop_sequences = ["<|user|>", "<|system|>"]
        if request.stop:
            if isinstance(request.stop, str):
                stop_sequences.append(request.stop)
            else:
                stop_sequences.extend(request.stop)
        
        # Generate chat completion
        with torch.no_grad():
            outputs = model.generate(
                input_ids,
                max_length=input_ids.shape[1] + request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=request.temperature > 0,
                pad_token_id=tokenizer.eos_token_id,
            )
        
        # Decode and extract assistant's response
        full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
        input_text = tokenizer.decode(input_ids[0], skip_special_tokens=True)
        
        # Extract only the new content generated by the model
        assistant_response = full_output[len(input_text):].strip()
        
        # Apply stop sequences
        for stop_seq in stop_sequences:
            if stop_seq in assistant_response:
                assistant_response = assistant_response[:assistant_response.index(stop_seq)]
        
        # Calculate token counts
        prompt_tokens = input_ids.shape[1]
        completion_tokens = outputs.shape[1] - input_ids.shape[1]
        
        # Update metrics
        if ENABLE_METRICS:
            PROMPT_TOKEN_COUNT.inc(prompt_tokens)
            TOKEN_COUNT.inc(completion_tokens)
        
        # Schedule memory cleanup for large models
        background_tasks.add_task(memory_manager.check_memory)
        
        # Return response
        response = {
            "id": f"chat-{str(uuid.uuid4())[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": MODEL_PATH,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": assistant_response
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
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Error generating chat response: {str(e)}")

# ===== Error handlers =====

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": f"error_{exc.status_code}"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "code": "internal_error"}
    )

# ===== Main entry point =====
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, log_level=os.environ.get("LOG_LEVEL", "info").lower())
