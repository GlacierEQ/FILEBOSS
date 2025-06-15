"""
Memory management utilities for DeepSeek-Coder.
"""

import os
import gc
import time
import logging
import threading
from typing import Optional, Dict, Any, List, Callable
import psutil

# Import PyTorch conditionally to allow using this module without GPU
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Memory manager for efficient GPU memory handling.
    Monitors memory usage and performs cleanup when needed.
    """
    
    def __init__(self, 
                 interval_seconds: int = 60, 
                 target_usage: float = 0.8, 
                 emergency_threshold: float = 0.95):
        """
        Initialize memory manager.
        
        Args:
            interval_seconds: Interval between memory checks in seconds
            target_usage: Target memory usage (0.0-1.0) to maintain
            emergency_threshold: Emergency threshold to trigger immediate cleanup
        """
        self.interval_seconds = interval_seconds
        self.target_usage = target_usage
        self.emergency_threshold = emergency_threshold
        self.stop_flag = threading.Event()
        self.thread = None
        self.last_cleanup_time = 0
        self.cleanup_callbacks: List[Callable[[], None]] = []
    
    def start(self):
        """Start the memory monitoring thread."""
        if self.thread is not None:
            return
        
        self.stop_flag.clear()
        self.thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="MemoryMonitor"
        )
        self.thread.start()
        logger.info(f"Memory manager started. Target usage: {self.target_usage:.1%}, Check interval: {self.interval_seconds}s")
    
    def stop(self):
        """Stop the memory monitoring thread."""
        if self.thread is None:
            return
        
        self.stop_flag.set()
        self.thread.join(timeout=5.0)
        self.thread = None
        logger.info("Memory manager stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while not self.stop_flag.is_set():
            try:
                # Check memory usage
                self.check_memory()
                
                # Sleep for the interval
                self.stop_flag.wait(self.interval_seconds)
            except Exception as e:
                logger.error(f"Error in memory monitor: {str(e)}")
                # Sleep a bit to avoid spam in case of recurring errors
                time.sleep(5)
    
    def check_memory(self):
        """
        Check current memory usage and cleanup if needed.
        Can be called manually for immediate check.
        """
        # Skip check if not enough time has passed since last cleanup
        if time.time() - self.last_cleanup_time < 10:  # Avoid too frequent cleanups
            return
        
        # Get GPU memory usage if available
        gpu_usage = self.get_gpu_memory_usage()
        
        if gpu_usage is not None:
            # For GPU, check against thresholds
            if gpu_usage >= self.emergency_threshold:
                logger.warning(f"Emergency memory cleanup triggered. GPU usage: {gpu_usage:.1%}")
                self.cleanup_memory(force=True)
            elif gpu_usage >= self.target_usage:
                logger.info(f"Memory cleanup triggered. GPU usage: {gpu_usage:.1%}")
                self.cleanup_memory()
        else:
            # For CPU-only, use system memory
            try:
                system_usage = psutil.virtual_memory().percent / 100.0
                if system_usage >= self.emergency_threshold:
                    logger.warning(f"Emergency memory cleanup triggered. System memory usage: {system_usage:.1%}")
                    self.cleanup_memory(force=True)
                elif system_usage >= self.target_usage:
                    logger.info(f"Memory cleanup triggered. System memory usage: {system_usage:.1%}")
                    self.cleanup_memory()
            except Exception as e:
                logger.error(f"Error checking system memory: {str(e)}")
    
    def get_gpu_memory_usage(self) -> Optional[float]:
        """
        Get current GPU memory usage as a fraction (0.0-1.0).
        
        Returns:
            GPU memory usage fraction or None if not available
        """
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return None
        
        try:
            # Get current and max GPU memory
            allocated = torch.cuda.memory_allocated()
            max_memory = torch.cuda.get_device_properties(0).total_memory
            
            # Calculate usage ratio
            return allocated / max_memory
        except Exception as e:
            logger.error(f"Error getting GPU memory: {str(e)}")
            return None
    
    def cleanup_memory(self, force: bool = False):
        """
        Clean up memory by releasing caches and forcing garbage collection.
        
        Args:
            force: Force more aggressive cleanup measures
        """
        self.last_cleanup_time = time.time()
        
        # Run custom cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in cleanup callback: {str(e)}")
        
        # Clear CUDA cache if available
        if TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
                logger.debug("CUDA cache cleared")
            except Exception as e:
                logger.error(f"Error clearing CUDA cache: {str(e)}")
        
        # Run garbage collection
        gc.collect()
        logger.debug("Garbage collection completed")
        
        if force:
            # More aggressive measures for emergency cleanup
            gc.collect(2)  # Collect all generations
            
            # On Linux, try to release memory to OS
            if hasattr(os, 'sync'):
                try:
                    os.sync()
                except Exception:
                    pass
    
    def register_cleanup_callback(self, callback: Callable[[], None]):
        """
        Register a custom cleanup callback.
        
        Args:
            callback: Function to call during cleanup
        """
        self.cleanup_callbacks.append(callback)
        logger.debug(f"Registered cleanup callback: {callback.__name__}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get detailed memory statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        stats = {
            "system": {
                "available": psutil.virtual_memory().available / (1024 ** 3),  # GB
                "total": psutil.virtual_memory().total / (1024 ** 3),  # GB
                "percent": psutil.virtual_memory().percent
            }
        }
        
        # Add GPU stats if available
        if TORCH_AVAILABLE and torch.cuda.is_available():
            stats["gpu"] = {
                "allocated": torch.cuda.memory_allocated() / (1024 ** 3),  # GB
                "reserved": torch.cuda.memory_reserved() / (1024 ** 3),  # GB
                "total": torch.cuda.get_device_properties(0).total_memory / (1024 ** 3),  # GB
            }
            stats["gpu"]["percent"] = (stats["gpu"]["allocated"] / stats["gpu"]["total"]) * 100
            
        return stats


# Create a global memory manager instance
_global_memory_manager = None

def get_memory_manager() -> MemoryManager:
    """
    Get or create the global memory manager instance.
    
    Returns:
        Global memory manager instance
    """
    global _global_memory_manager
    if _global_memory_manager is None:
        _global_memory_manager = MemoryManager()
    return _global_memory_manager
