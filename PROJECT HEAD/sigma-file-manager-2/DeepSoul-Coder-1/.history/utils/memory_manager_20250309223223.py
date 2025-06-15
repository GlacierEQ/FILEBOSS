"""
Memory Manager - Utility for monitoring and managing memory usage
"""
import os
import gc
import sys
import torch
import psutil
import logging
import threading
import time
from typing import Dict, List, Union, Optional, Callable, Tuple, Any
from pathlib import Path

logger = logging.getLogger("DeepSoul-MemoryManager")

class MemoryManager:
    """
    Memory Manager for monitoring and controlling memory usage.
    Provides utilities for preventing OOM errors and managing resources efficiently.
    """
    
    def __init__(self, 
                warning_threshold: float = 0.85,
                critical_threshold: float = 0.95,
                gpu_warning_threshold: float = 0.85,
                gpu_critical_threshold: float = 0.95,
                check_interval: float = 5.0,
                enable_monitoring: bool = True):
        """
        Initialize the memory manager
        
        Args:
            warning_threshold: System RAM usage threshold for warnings (0.0-1.0)
            critical_threshold: System RAM usage threshold for critical actions (0.0-1.0)
            gpu_warning_threshold: GPU memory usage threshold for warnings (0.0-1.0)
            gpu_critical_threshold: GPU memory usage threshold for critical actions (0.0-1.0)
            check_interval: Interval in seconds for automatic monitoring
            enable_monitoring: Whether to start the monitoring thread
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.gpu_warning_threshold = gpu_warning_threshold
        self.gpu_critical_threshold = gpu_critical_threshold
        self.check_interval = check_interval
        
        # Memory usage history for tracking trends
        self.ram_history = []
        self.gpu_history = []
        self.history_max_size = 20
        
        # Event hooks
        self.warning_hooks = []
        self.critical_hooks = []
        
        # Monitoring thread
        self.monitor_thread = None
        self.monitoring = False
        
        # Device information
        self.has_gpu = torch.cuda.is_available()
        self.gpu_count = torch.cuda.device_count() if self.has_gpu else 0
        
        # Create directory for memory dumps
        self.memory_dump_dir = Path("memory_dumps")
        self.memory_dump_dir.mkdir(exist_ok=True)
        
        if enable_monitoring:
            self.start_monitoring()
    
    def start_monitoring(self) -> None:
        """Start the memory monitoring thread"""
        if self.monitor_thread is not None and self.monitor_thread.is_alive():
            logger.warning("Memory monitoring thread is already running")
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="MemoryMonitor"
        )
        self.monitor_thread.start()
        logger.info("Memory monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop the memory monitoring thread"""
        self.monitoring = False
        if self.monitor_thread is not None and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
            logger.info("Memory monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Internal monitoring loop that runs in a separate thread"""
        while self.monitoring:
            try:
                # Check memory usage
                system_usage = self.get_system_memory_usage()
                
                # Add to history
                self.ram_history.append(system_usage)
                if len(self.ram_history) > self.history_max_size:
                    self.ram_history = self.ram_history[-self.history_max_size:]
                
                # Check for warning threshold
                if system_usage > self.warning_threshold:
                    logger.warning(f"High RAM usage detected: {system_usage:.1%}")
                    self._run_warning_hooks({"ram_usage": system_usage})
                
                # Check for critical threshold
                if system_usage > self.critical_threshold:
                    logger.critical(f"Critical RAM usage detected: {system_usage:.1%}")
                    self._run_critical_hooks({"ram_usage": system_usage})
                    # Force garbage collection
                    gc.collect()
                
                # Check GPU memory if available
                if self.has_gpu:
                    for i in range(self.gpu_count):
                        gpu_usage = self.get_gpu_memory_usage(i)
                        
                        # Add to history
                        if i == 0:  # Only track primary GPU for now
                            self.gpu_history.append(gpu_usage)
                            if len(self.gpu_history) > self.history_max_size:
                                self.gpu_history = self.gpu_history[-self.history_max_size:]
                        
                        # Check for warning threshold
                        if gpu_usage > self.gpu_warning_threshold:
                            logger.warning(f"High GPU {i} memory usage detected: {gpu_usage:.1%}")
                            self._run_warning_hooks({"gpu_id": i, "gpu_usage": gpu_usage})
                        
                        # Check for critical threshold
                        if gpu_usage > self.gpu_critical_threshold:
                            logger.critical(f"Critical GPU {i} memory usage detected: {gpu_usage:.1%}")
                            self._run_critical_hooks({"gpu_id": i, "gpu_usage": gpu_usage})
                            # Clear CUDA cache for this device
                            torch.cuda.empty_cache()
            
            except Exception as e:
                logger.error(f"Error in memory monitoring: {str(e)}")
            
            # Sleep for check interval
            time.sleep(self.check_interval)
    
    def _run_warning_hooks(self, data: Dict[str, Any]) -> None:
        """Run all registered warning hooks"""
        for hook in self.warning_hooks:
            try:
                hook(data)
            except Exception as e:
                logger.error(f"Error running warning hook: {str(e)}")
    
    def _run_critical_hooks(self, data: Dict[str, Any]) -> None:
        """Run all registered critical hooks"""
        for hook in self.critical_hooks:
            try:
                hook(data)
            except Exception as e:
                logger.error(f"Error running critical hook: {str(e)}")
    
    def register_warning_hook(self, hook: Callable[[Dict[str, Any]], None]) -> None:
        """Register a hook to be called when memory usage exceeds warning threshold"""
        self.warning_hooks.append(hook)
    
    def register_critical_hook(self, hook: Callable[[Dict[str, Any]], None]) -> None:
        """Register a hook to be called when memory usage exceeds critical threshold"""
        self.critical_hooks.append(hook)
    
    def get_system_memory_usage(self) -> float:
        """
        Get current system memory usage as a fraction (0.0-1.0)
        
        Returns:
            Float representing memory usage (0.0-1.0)
        """
        try:
            # Get memory information
            memory = psutil.virtual_memory()
            return memory.percent / 100.0
        except Exception as e:
            logger.error(f"Error getting system memory usage: {str(e)}")
            return 0.0
    
    def get_gpu_memory_usage(self, device_id: int = 0) -> float:
        """
        Get current GPU memory usage as a fraction (0.0-1.0)
        
        Args:
            device_id: GPU device ID
            
        Returns:
            Float representing memory usage (0.0-1.0)
        """
        if not self.has_gpu:
            return 0.0
            
        try:
            # Get GPU memory information
            torch.cuda.synchronize(device_id)
            allocated = torch.cuda.memory_allocated(device_id)
            reserved = torch.cuda.memory_reserved(device_id)
            total = torch.cuda.get_device_properties(device_id).total_memory
            
            # Calculate usage
            usage = allocated / total
            return usage
        except Exception as e:
            logger.error(f"Error getting GPU memory usage: {str(e)}")
            return 0.0
    
    def check_available_memory(self, required_bytes: int) -> bool:
        """
        Check if enough system memory is available for operation
        
        Args:
            required_bytes: Number of bytes required
            
        Returns:
            True if memory is available, False otherwise
        """
        try:
            memory = psutil.virtual_memory()
            return memory.available >= required_bytes
        except Exception as e:
            logger.error(f"Error checking available memory: {str(e)}")
            return False
    
    def check_available_gpu_memory(self, required_bytes: int, device_id: int = 0) -> bool:
        """
        Check if enough GPU memory is available for operation
        
        Args:
            required_bytes: Number of bytes required
            device_id: GPU device ID
            
        Returns:
            True if memory is available, False otherwise
        """
        if not self.has_gpu:
            return False
            
        try:
            # Get GPU memory information
            torch.cuda.synchronize(device_id)
            allocated = torch.cuda.memory_allocated(device_id)
            total = torch.cuda.get_device_properties(device_id).total_memory
            
            # Calculate available memory
            available = total - allocated
            return available >= required_bytes
        except Exception as e:
            logger.error(f"Error checking available GPU memory: {str(e)}")
            return False
    
    def estimate_tensor_memory(self, shape: List[int], dtype=torch.float32) -> int:
        """
        Estimate memory usage of a tensor
        
        Args:
            shape: Tensor shape
            dtype: Tensor data type
            
        Returns:
            Estimated memory in bytes
        """
        # Get element size for the data type
        element_size = {
            torch.float32: 4,
            torch.float16: 2,
            torch.int64: 8,
            torch.int32: 4,
            torch.int16: 2,
            torch.int8: 1,
            torch.uint8: 1,
            torch.bool: 1
        }.get(dtype, 4)  # Default to float32 size if unknown
        
        # Calculate total elements
        total_elements = 1
        for dim in shape:
            total_elements *= dim
        
        # Calculate memory size
        return total_elements * element_size
    
    def optimize_for_inference(self, model: torch.nn.Module, device: str = 'cuda') -> torch.nn.Module:
        """
        Optimize a PyTorch model for inference to reduce memory usage
        
        Args:
            model: PyTorch model
            device: Device to optimize for
            
        Returns:
            Optimized model
        """
        # Move model to CPU first
        model = model.cpu()
        
        # Run garbage collection to free memory
        gc.collect()
        torch.cuda.empty_cache()
        
        # Use half precision if on CUDA
        if device == 'cuda':
            model = model.half()
        
        # Move model to device
        model = model.to(device)
        
        # Set to evaluation mode to disable dropout and batch norm
        model.eval()
        
        return model
    
    def memory_efficient_inference(self, model: torch.nn.Module, inputs: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Run inference with memory efficiency
        
        Args:
            model: PyTorch model
            inputs: Model inputs
            
        Returns:
            Model outputs
        """
        # Clear cache before inference
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        # Run garbage collection
        gc.collect()
        
        try:
            # Set to no_grad to save memory
            with torch.no_grad():
                outputs = model(**inputs)
                
            return outputs
        except RuntimeError as e:
            # Check if error is OOM
            if "CUDA out of memory" in str(e):
                logger.error("CUDA out of memory during inference")
                
                # Try to recover
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    gc.collect()
                
                # Try with CPU
                device = next(model.parameters()).device
                cpu_inputs = {k: v.cpu() for k, v in inputs.items()}
                
                logger.warning("Retrying inference on CPU")
                with torch.no_grad():
                    model = model.cpu()
                    outputs = model(**cpu_inputs)
                    model = model.to(device)
                    
                return outputs
            else:
                raise
    
    def clear_memory(self, move_models_to_cpu: bool = False) -> None:
        """
        Clear memory by running garbage collection and emptying CUDA cache
        
        Args:
            move_models_to_cpu: Whether to move all loaded models to CPU
        """
        if move_models_to_cpu:
            # Find all torch modules in globals
            import gc
            for obj in gc.get_objects():
                try:
                    if isinstance(obj, torch.nn.Module):
                        obj.cpu()
                except Exception:
                    pass
        
        # Run garbage collection
        gc.collect()
        
        # Empty CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    def memory_dump(self, tag: str = "") -> str:
        """
        Create a memory dump for debugging
        
        Args:
            tag: Optional tag for the dump file
            
        Returns:
            Path to the memory dump file
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        tag_str = f"_{tag}" if tag else ""
        dump_file = self.memory_dump_dir / f"memory_dump{tag_str}_{timestamp}.txt"
        
        try:
            with open(dump_file, "w") as f:
                # System information
                f.write("=== SYSTEM INFORMATION ===\n")
                f.write(f"Python version: {sys.version}\n")
                f.write(f"PyTorch version: {torch.__version__}\n")
                f.write(f"CUDA available: {torch.cuda.is_available()}\n")
                if torch.cuda.is_available():
                    f.write(f"CUDA version: {torch.version.cuda}\n")
                    f.write(f"GPU count: {torch.cuda.device_count()}\n")
                    for i in range(torch.cuda.device_count()):
                        f.write(f"GPU {i}: {torch.cuda.get_device_name(i)}\n")
                
                # Memory usage
                f.write("\n=== MEMORY USAGE ===\n")
                memory = psutil.virtual_memory()
                f.write(f"Total RAM: {memory.total / (1024**3):.2f} GB\n")
                f.write(f"Available RAM: {memory.available / (1024**3):.2f} GB\n")
                f.write(f"Used RAM: {memory.used / (1024**3):.2f} GB\n")
                f.write(f"RAM Usage: {memory.percent}%\n")
                
                if torch.cuda.is_available():
                    for i in range(torch.cuda.device_count()):
                        torch.cuda.synchronize(i)
                        allocated = torch.cuda.memory_allocated(i) / (1024**3)
                        reserved = torch.cuda.memory_reserved(i) / (1024**3)
                        total = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                        f.write(f"\nGPU {i} Memory:\n")
                        f.write(f"  Total: {total:.2f} GB\n")
                        f.write(f"  Allocated: {allocated:.2f} GB\n")
                        f.write(f"  Reserved: {reserved:.2f} GB\n")
                        f.write(f"  Usage: {(allocated / total) * 100:.1f}%\n")
                
                # Process information
                f.write("\n=== PROCESS INFORMATION ===\n")
                process = psutil.Process(os.getpid())
                f.write(f"Process ID: {process.pid}\n")
                f.write(f"Process memory info: {process.memory_info()}\n")
                f.write(f"CPU usage: {process.cpu_percent()}%\n")
                f.write(f"Memory usage: {process.memory_percent()}%\n")
                f.write(f"Threads: {process.num_threads()}\n")
                
                # Current objects in memory
                f.write("\n=== SIGNIFICANT OBJECTS IN MEMORY ===\n")
                size_threshold = 10 * 1024 * 1024  # 10 MB
                objects = []
                for obj in gc.get_objects():
                    try:
                        if torch.is_tensor(obj):
                            obj_size = obj.element_size() * obj.nelement()
                            if obj_size > size_threshold:
                                objects.append((type(obj), obj.shape, obj.dtype, obj_size, obj.device if hasattr(obj, 'device') else 'N/A'))
                    except Exception:
                        pass
                
                objects.sort(key=lambda x: x[3], reverse=True)
                for i, (obj_type, obj_shape, obj_dtype, obj_size, obj_device) in enumerate(objects[:20]):
                    f.write(f"{i+1}. Type: {obj_type}, Shape: {obj_shape}, Dtype: {obj_dtype}, Size: {obj_size / (1024**2):.2f} MB, Device: {obj_device}\n")
            
            return str(dump_file)
        except Exception as e:
            logger.error(f"Error creating memory dump: {str(e)}")
            return ""

# Global memory manager instance for easy access
memory_manager = MemoryManager()

def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance"""
    global memory_manager
    return memory_manager

def setup_memory_protection(critical_hook: Callable = None, warning_hook: Callable = None) -> MemoryManager:
    """
    Set up memory protection with custom hooks
    
    Args:
        critical_hook: Hook called when critical memory threshold is reached
        warning_hook: Hook called when warning memory threshold is reached
    
    Returns:
        Memory manager instance
    """
    global memory_manager
    
    # Register hooks if provided
    if critical_hook:
        memory_manager.register_critical_hook(critical_hook)
    
    if warning_hook:
        memory_manager.register_warning_hook(warning_hook)
    
    # Default critical hook if none provided
    if not critical_hook:
        memory_manager.register_critical_hook(lambda data: torch.cuda.empty_cache() if torch.cuda.is_available() else None)
    
    return memory_manager

# Example memory protection hooks
def default_warning_hook(data: Dict[str, Any]) -> None:
    """Default warning hook"""
    if "gpu_usage" in data:
        logger.warning(f"High GPU memory usage detected: {data['gpu_usage']:.1%}")
        # Log warning but don't take action
    elif "ram_usage" in data:
        logger.warning(f"High RAM usage detected: {data['ram_usage']:.1%}")
        # Maybe clean some caches

def default_critical_hook(data: Dict[str, Any]) -> None:
    """Default critical hook"""
    if "gpu_usage" in data:
        logger.critical(f"Critical GPU memory usage detected: {data['gpu_usage']:.1%}")
        # Clear CUDA cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        # Perform garbage collection
        gc.collect()
    elif "ram_usage" in data:
        logger.critical(f"Critical RAM usage detected: {data['ram_usage']:.1%}")
        # Perform aggressive memory cleanup
        gc.collect()
        # Create memory dump for debugging
        memory_manager.memory_dump("critical_ram")

# Set up default hooks
setup_memory_protection(
    critical_hook=default_critical_hook,
    warning_hook=default_warning_hook
)

if __name__ == "__main__":
    # Example usage when run directly
    logging.basicConfig(level=logging.INFO)
    print("Memory Manager Test")
    
    # Get memory information
    mm = get_memory_manager()
    print(f"System memory usage: {mm.get_system_memory_usage():.1%}")
    
    if torch.cuda.is_available():
        print(f"GPU count: {mm.gpu_count}")
        for i in range(mm.gpu_count):
            print(f"GPU {i} memory usage: {mm.get_gpu_memory_usage(i):.1%}")
    
    # Create memory dump
    dump_path = mm.memory_dump("test")
    print(f"Memory dump created: {dump_path}")
