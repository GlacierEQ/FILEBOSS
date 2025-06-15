"""
OOM Protected Execution - Decorator and utilities for OOM-protected code execution
"""
import gc
import sys
import torch
import logging
import functools
import traceback
from typing import Callable, Any, Dict, Optional, Union, List, Tuple

# Add parent directory to path for imports
sys.path.append('..')

from utils.memory_manager import get_memory_manager

logger = logging.getLogger('DeepSoul-OOMProtection')

class OOMProtectionError(RuntimeError):
    """Exception raised when OOM protection fails to recover"""
    pass

def oom_protected(func=None, *, retry_on_cpu=True, fallback_func=None, max_retries=2):
    """
    Decorator for OOM-protected function execution
    
    Args:
        func: The function to decorate
        retry_on_cpu: Whether to retry on CPU if CUDA OOM occurs
        fallback_func: Optional fallback function to call if execution fails
        max_retries: Maximum number of retries
        
    Returns:
        Decorated function with OOM protection
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            memory_manager = get_memory_manager()
            retries = 0
            
            while True:
                try:
                    # Clear memory before execution
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    gc.collect()
                    
                    # Execute function
                    return f(*args, **kwargs)
                    
                except RuntimeError as e:
                    # Check if error is CUDA OOM
                    if "CUDA out of memory" in str(e) and torch.cuda.is_available():
                        retries += 1
                        logger.warning(f"CUDA OOM detected in {f.__name__}, retry {retries}/{max_retries}")
                        
                        # Create memory dump for debugging
                        memory_manager.memory_dump(f"oom_{f.__name__}")
                        
                        # Clear memory
                        torch.cuda.empty_cache()
                        gc.collect()
                        
                        if retries >= max_retries:
                            # Try on CPU if enabled
                            if retry_on_cpu:
                                logger.warning(f"Moving execution to CPU for {f.__name__}")
                                
                                # Move tensors in args and kwargs to CPU
                                cpu_args = _tensors_to_device(args, 'cpu')
                                cpu_kwargs = _tensors_to_device(kwargs, 'cpu')
                                
                                try:
                                    result = f(*cpu_args, **cpu_kwargs)
                                    
                                    # Move result back to original device if possible
                                    device = _get_preferred_device(args, kwargs)
                                    if device.type == 'cuda' and torch.cuda.is_available():
                                        result = _tensors_to_device(result, device)
                                    
                                    return result
                                except Exception as cpu_err:
                                    logger.error(f"CPU fallback failed: {str(cpu_err)}")
                                    
                                    # Try fallback function if provided
                                    if fallback_func is not None:
                                        logger.warning(f"Using fallback function for {f.__name__}")
                                        return fallback_func(*args, **kwargs)
                                    
                                    raise OOMProtectionError(f"OOM protection failed for {f.__name__}: {str(e)}")
                            # If retry_on_cpu is False, use fallback or raise exception
                            elif fallback_func is not None:
                                logger.warning(f"Using fallback function for {f.__name__}")
                                return fallback_func(*args, **kwargs)
                            else:
                                raise OOMProtectionError(f"OOM protection failed for {f.__name__} after {retries} retries: {str(e)}")
                        else:
                            # Continue with next retry
                            continue
                    else:
                        # Not an OOM error, re-raise
                        raise
                
                except Exception as e:
                    # Handle other exceptions
                    logger.error(f"Error in {f.__name__}: {str(e)}")
                    
                    # Try fallback function if provided
                    if fallback_func is not None:
                        logger.warning(f"Using fallback function for {f.__name__} due to error: {str(e)}")
                        return fallback_func(*args, **kwargs)
                    
                    # Re-raise the exception
                    raise
        
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)

def _tensors_to_device(obj, device):
    """
    Move all tensors in an object to the specified device
    
    Args:
        obj: Object containing tensors
        device: Target device
        
    Returns:
        Object with tensors moved to device
    """
    if torch.is_tensor(obj):
        try:
            return obj.to(device)
        except Exception:
            return obj
            
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_tensors_to_device(x, device) for x in obj)
        
    elif isinstance(obj, dict):
        return {k: _tensors_to_device(v, device) for k, v in obj.items()}
        
    return obj

def _get_preferred_device(args, kwargs):
    """
    Get the preferred device from function arguments
    
    Args:
        args: Function positional arguments
        kwargs: Function keyword arguments
        
    Returns:
        Preferred device (defaults to CUDA if available)
    """
    # Check args for tensors
    for arg in args:
        if torch.is_tensor(arg) and arg.device.type == 'cuda':
            return arg.device
    
    # Check kwargs for tensors
    for arg in kwargs.values():
        if torch.is_tensor(arg) and arg.device.type == 'cuda':
            return arg.device
    
    # Default to cuda:0 if available
    return torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

def estimate_memory_usage(func, sample_input, dry_run=True):
    """
    Estimate memory usage of a function with given input
    
    Args:
        func: Function to estimate
        sample_input: Sample input for the function
        dry_run: Whether to perform a dry run first
        
    Returns:
        Dictionary with memory usage information
    """
    memory_manager = get_memory_manager()
    
    # Ensure we're on CUDA for measurements
    if not torch.cuda.is_available():
        return {"status": "error", "reason": "CUDA not available"}
    
    # Clear memory before measurement
    torch.cuda.empty_cache()
    gc.collect()
    
    # Capture initial memory state
    torch.cuda.synchronize()
    mem_before = torch.cuda.memory_allocated()
    
    # Perform a dry run if requested (to allocate caches, etc.)
    if dry_run:
        try:
            with torch.no_grad():
                _ = func(sample_input)
            
            # Clear memory after dry run
            torch.cuda.empty_cache()
            gc.collect()
            torch.cuda.synchronize()
            mem_before = torch.cuda.memory_allocated()
        except Exception as e:
            return {"status": "error", "reason": f"Dry run failed: {str(e)}"}
    
    # Measure actual execution
    try:
        with torch.no_grad():
            start_time = time.time()
            _ = func(sample_input)
            execution_time = time.time() - start_time
        
        # Measure peak memory
        torch.cuda.synchronize()
        mem_after = torch.cuda.memory_allocated()
        peak_mem = torch.cuda.max_memory_allocated()
        
        return {
            "status": "success",
            "memory_before_mb": mem_before / (1024 * 1024),
            "memory_after_mb": mem_after / (1024 * 1024),
            "memory_used_mb": (mem_after - mem_before) / (1024 * 1024),
            "peak_memory_mb": peak_mem / (1024 * 1024),
            "execution_time_sec": execution_time
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "reason": str(e),
            "memory_before_mb": mem_before / (1024 * 1024)
        }

class MemoryEfficientContext:
    """
    Context manager for memory-efficient execution
    
    Usage:
    with MemoryEfficientContext():
        # Memory-intensive code here
    """
    
    def __init__(self, clear_cuda_cache=True, run_gc=True, dump_on_error=True):
        """
        Initialize the context manager
        
        Args:
            clear_cuda_cache: Whether to clear CUDA cache before and after execution
            run_gc: Whether to run garbage collection before and after execution
            dump_on_error: Whether to create memory dump if error occurs
        """
        self.clear_cuda_cache = clear_cuda_cache and torch.cuda.is_available()
        self.run_gc = run_gc
        self.dump_on_error = dump_on_error
        self.memory_manager = get_memory_manager()
    
    def __enter__(self):
        """Enter the context manager"""
        # Clear memory before execution
        if self.clear_cuda_cache:
            torch.cuda.empty_cache()
        if self.run_gc:
            gc.collect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager"""
        # Handle exceptions
        if exc_type is not None and "CUDA out of memory" in str(exc_val) and self.dump_on_error:
            # Create memory dump for debugging
            self.memory_manager.memory_dump("context_manager_oom")
        
        # Clear memory after execution
        if self.clear_cuda_cache:
            torch.cuda.empty_cache()
        if self.run_gc:
            gc.collect()
        
        # Don't suppress the exception
        return False

def adaptive_batch_size(start_size=16, min_size=1, max_size=128):
    """
    Decorator for functions that can adapt their batch size based on available memory
    
    Usage:
    @adaptive_batch_size(start_size=16, min_size=1, max_size=128)
    def process_batch(batch_size, data):
        # Process with dynamic batch size
        pass
    
    Args:
        start_size: Initial batch size
        min_size: Minimum batch size
        max_size: Maximum batch size
        
    Returns:
        Decorated function with adaptive batch sizing
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_size = start_size
            
            while current_size >= min_size:
                try:
                    # Try with current batch size
                    kwargs['batch_size'] = current_size
                    return func(*args, **kwargs)
                    
                except RuntimeError as e:
                    # Reduce batch size if CUDA OOM
                    if "CUDA out of memory" in str(e) and torch.cuda.is_available():
                        prev_size = current_size
                        current_size = max(min_size, current_size // 2)
                        logger.warning(f"CUDA OOM detected. Reducing batch size from {prev_size} to {current_size}")
                        
                        # Clear memory
                        torch.cuda.empty_cache()
                        gc.collect()
                        
                        if current_size < min_size:
                            raise OOMProtectionError(f"Batch size {current_size} below minimum {min_size}")
                    else:
                        # Not an OOM error, re-raise
                        raise
            
            # If we get here, we've exhausted all batch sizes
            raise OOMProtectionError(f"Failed to find working batch size above minimum {min_size}")
        
        return wrapper
    return decorator

# Convenience function for memory-intensive operations
def run_with_oom_protection(func, *args, retry_on_cpu=True, **kwargs):
    """
    Run a function with OOM protection without using the decorator
    
    Args:
        func: Function to run
        retry_on_cpu: Whether to retry on CPU if CUDA OOM occurs
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        Function result
    """
    protected_func = oom_protected(retry_on_cpu=retry_on_cpu)(func)
    return protected_func(*args, **kwargs)
