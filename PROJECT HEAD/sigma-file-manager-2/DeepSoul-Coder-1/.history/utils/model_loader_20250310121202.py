"""
Model loader utility for DeepSeek-Coder.
Provides functions to load and optimize models for inference.
"""

import os
import sys
import logging
import torch
from typing import Tuple, Any, Optional, Dict
from transformers import AutoTokenizer, AutoModelForCausalLM

# Configure logging
logger = logging.getLogger(__name__)

def load_model_and_tokenizer(
    model_path: str, 
    device: str = "auto",
    precision: str = "auto",
    trust_remote_code: bool = True,
    use_flash_attention: bool = True,
    use_torch_compile: bool = True
) -> Tuple[Any, Any]:
    """
    Load a model and tokenizer for DeepSeek-Coder.
    
    Args:
        model_path: Path or HF model identifier
        device: Device to load the model on ('auto', 'cpu', 'cuda', 'cuda:0', etc.)
        precision: Precision to use ('auto', 'fp32', 'fp16', 'bf16')
        trust_remote_code: Whether to trust remote code in HF models
        use_flash_attention: Whether to use Flash Attention if available
        use_torch_compile: Whether to use torch.compile if available
        
    Returns:
        Tuple of (model, tokenizer)
    """
    start_time = torch.cuda.Event(enable_timing=True)
    end_time = torch.cuda.Event(enable_timing=True)
    
    # Determine device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    logger.info(f"Loading model from {model_path} on {device}")
    
    # Determine torch dtype based on precision and device capabilities
    if precision == "auto":
        if device.startswith("cuda") and torch.cuda.is_available():
            if torch.cuda.is_bf16_supported():
                dtype = torch.bfloat16
                logger.info("Using bfloat16 precision")
            else:
                dtype = torch.float16
                logger.info("Using float16 precision")
        else:
            dtype = torch.float32
            logger.info("Using float32 precision")
    elif precision == "fp16":
        dtype = torch.float16
    elif precision == "bf16":
        dtype = torch.bfloat16
    else:  # fp32
        dtype = torch.float32
    
    # Configure Flash Attention if available and requested
    if use_flash_attention and device != "cpu":
        try:
            from transformers.utils import is_flash_attn_available
            if is_flash_attn_available():
                os.environ["TRANSFORMERS_ATTENTION_IMPLEMENTATION"] = "flash_attention_2"
                logger.info("Flash Attention enabled")
        except ImportError:
            logger.warning("Could not check Flash Attention availability")
    
    # Set CUDA optimizations
    if device.startswith("cuda") and torch.cuda.is_available():
        # Set PyTorch CUDA optimizations
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        
        # Enable Scaled Dot Product attention
        torch.backends.cuda.enable_mem_efficient_sdp(True)
        torch.backends.cuda.enable_flash_sdp(True)
        torch.backends.cuda.enable_math_sdp(True)
        
        # Memory optimizations
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"

    # Load tokenizer
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_path, 
            trust_remote_code=trust_remote_code
        )
        logger.info(f"Tokenizer loaded: {type(tokenizer).__name__}")
    except Exception as e:
        logger.error(f"Error loading tokenizer: {str(e)}")
        raise
    
    # Start timing model load if on CUDA
    if device.startswith("cuda") and torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        start_time.record()
    
    # Load model with optimizations
    try:
        model_kwargs = {
            "torch_dtype": dtype,
            "trust_remote_code": trust_remote_code,
        }
        
        # Set device map according to device choice
        if device == "cpu":
            model_kwargs["device_map"] = "cpu"
        elif torch.cuda.device_count() > 1:
            model_kwargs["device_map"] = "auto"
            logger.info(f"Using auto device map with {torch.cuda.device_count()} GPUs")
        else:
            model_kwargs["device_map"] = device
        
        model = AutoModelForCausalLM.from_pretrained(model_path, **model_kwargs)
        
        # Apply torch.compile if available and requested
        if use_torch_compile and hasattr(torch, "compile") and device != "cpu":
            try:
                logger.info("Applying torch.compile...")
                model = torch.compile(model, mode="reduce-overhead")
                logger.info("Model compiled successfully")
            except Exception as e:
                logger.warning(f"Failed to apply torch.compile: {str(e)}")
        
        # End timing and report memory usage if on CUDA
        if device.startswith("cuda") and torch.cuda.is_available():
            end_time.record()
            torch.cuda.synchronize()
            load_time = start_time.elapsed_time(end_time) / 1000  # convert ms to s
            
            # Report memory usage
            peak_memory = torch.cuda.max_memory_allocated() / (1024 ** 3)  # GB
            current_memory = torch.cuda.memory_allocated() / (1024 ** 3)  # GB
            logger.info(f"Model loaded in {load_time:.2f}s, peak memory: {peak_memory:.2f} GB, current: {current_memory:.2f} GB")
        
        model.eval()  # Set model to evaluation mode
        logger.info(f"Model loaded: {model.__class__.__name__}")
        
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise

def unload_model():
    """
    Unload model to free up GPU memory.
    """
    import gc
    
    # Clear CUDA cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # Force garbage collection
    gc.collect()
    
    logger.info("Model unloaded and memory cleared")
