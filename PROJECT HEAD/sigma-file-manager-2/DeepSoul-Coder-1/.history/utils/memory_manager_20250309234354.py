"""
Memory Manager - Monitor and manage memory usage
"""
import os
import gc
import sys
import time
import json
import psutil
import logging
import threading
from typing import Dict, List, Optional, Union, Any, Callable
from datetime import datetime
from pathlib import Path

# Import torch if available
try:
    import torch
    import torch.cuda
    HAS_TORCH = True
    
    # Check if CUDA is available
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    HAS_TORCH = False
    CUDA_AVAILABLE = False

# Import NVML if available
try:
    import py3nvml as pynvml
    HAS_NVML = True
except ImportError:
    HAS_NVML = False

logger = logging.getLogger("DeepSoul-MemoryManager")

class MemoryManager:
    """
    Monitor and manage memory usage for both system RAM and GPU
    
    This class provides utilities for tracking memory usage, detecting OOM conditions,
    and implementing memory protection strategies.
    """
    
    def __init__(self):
        """Initialize the memory manager"""
        # Memory monitoring settings
        self.ram_warning_threshold = 0.85
        self.ram_critical_threshold = 0.95
        self.gpu_warning_threshold = 0.85
        self.gpu_critical_threshold = 0.95
        
        # Memory monitoring thread
        self.monitor_thread = None
        self.monitoring = False
        self.check_interval = 5.0  # seconds
        
        # Memory usage history
        self.history = {
            "timestamps": [],
            "ram_usage": [],
            "gpu_usage": [],
            "warnings": []
        }
        
        # Memory dump settings
        self.memory_dump_enabled = True
        self.memory_dump_dir = "memory_dumps"
        self.last_dump_time = 0
        self.min_dump_interval = 60  # seconds
        
        # Warning/critical hooks
        self.warning_hook = None
        self.critical_hook = None
        
        # Initialize NVML if available
        if HAS_NVML:
            try:
                pynvml.nvmlInit()
                self.nvml_initialized = True
            except Exception as e:
                logger.warning(f"Failed to initialize NVML: {e}")
                self.nvml_initialized = False
        else:
            self.nvml_initialized = False
    
    def start_monitoring(self):
        """Start background memory monitoring"""
        if self.monitoring:
            logger.warning("Memory monitoring already started")
            return
            
        self.monitoring = True
        
        # Create monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="MemoryMonitorThread",
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop background memory monitoring"""
        if not self.monitoring:
            return
            
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            
        logger.info("Memory monitoring stopped")
    
    def _monitor_loop(self):
        """Background memory monitoring loop"""
        while self.monitoring:
            try:
                self._check_memory()
            except Exception as e:
                logger.error(f"Error in memory monitoring: {e}")
            
            time.sleep(self.check_interval)
    
    def _check_memory(self):
        """Check current memory usage and trigger warnings if needed"""
        # Get current usage
        ram_usage = self.get_system_memory_usage()
        gpu_usage = self.get_gpu_memory_usage()
        
        # Update history
        timestamp = time.time()
        self.history["timestamps"].append(timestamp)
        self.history["ram_usage"].append(ram_usage)
        self.history["gpu_usage"].append(gpu_usage)
        
        # Trim history if too long
        max_history = 1000
        if len(self.history["timestamps"]) > max_history:
            for key in self.history:
                if isinstance(self.history[key], list):
                    self.history[key] = self.history[key][-max_history:]
        
        # Check for warning conditions
        if ram_usage > self.ram_critical_threshold:
            self._handle_ram_critical(ram_usage)
        elif ram_usage > self.ram_warning_threshold:
            self._handle_ram_warning(ram_usage)
            
        if gpu_usage > self.gpu_critical_threshold:
            self._handle_gpu_critical(gpu_usage)
        elif gpu_usage > self.gpu_warning_threshold:
            self._handle_gpu_warning(gpu_usage)
    
    def _handle_ram_warning(self, usage):
        """Handle RAM usage warning"""
        message = f"RAM usage warning: {usage:.1%}"
        logger.warning(message)
        
        # Add to warnings history
        self.history["warnings"].append({
            "time": time.time(),
            "type": "ram_warning",
            "usage": usage
        })
        
        # Call warning hook if defined
        if self.warning_hook:
            try:
                self.warning_hook({"ram_usage": usage})
            except Exception as e:
                logger.error(f"Error in RAM warning hook: {e}")
    
    def _handle_ram_critical(self, usage):
        """Handle critical RAM usage"""
        message = f"CRITICAL RAM usage: {usage:.1%}"
        logger.critical(message)
        
        # Add to warnings history
        self.history["warnings"].append({
            "time": time.time(),
            "type": "ram_critical",
            "usage": usage
        })
        
        # Create memory dump
        self.memory_dump("ram_critical")
        
        # Force garbage collection
        gc.collect()
        
        # Clear torch cache if available
        if HAS_TORCH and CUDA_AVAILABLE:
            torch.cuda.empty_cache()
        
        # Call critical hook if defined
        if self.critical_hook:
            try:
                self.critical_hook({"ram_usage": usage})
            except Exception as e:
                logger.error(f"Error in RAM critical hook: {e}")
    
    def _handle_gpu_warning(self, usage):
        """Handle GPU usage warning"""
        message = f"GPU memory usage warning: {usage:.1%}"
        logger.warning(message)
        
        # Add to warnings history
        self.history["warnings"].append({
            "time": time.time(),
            "type": "gpu_warning",
            "usage": usage
        })
        
        # Call warning hook if defined
        if self.warning_hook:
            try:
                gpu_id = 0  # Default to first GPU
                self.warning_hook({"gpu_usage": usage, "gpu_id": gpu_id})
            except Exception as e:
                logger.error(f"Error in GPU warning hook: {e}")
    
    def _handle_gpu_critical(self, usage):
        """Handle critical GPU usage"""
        message = f"CRITICAL GPU memory usage: {usage:.1%}"
        logger.critical(message)
        
        # Add to warnings history
        self.history["warnings"].append({
            "time": time.time(),
            "type": "gpu_critical",
            "usage": usage
        })
        
        # Create memory dump
        self.memory_dump("gpu_critical")
        
        # Clear torch cache if available
        if HAS_TORCH and CUDA_AVAILABLE:
            torch.cuda.empty_cache()
        
        # Call critical hook if defined
        if self.critical_hook:
            try:
                gpu_id = 0  # Default to first GPU
                self.critical_hook({"gpu_usage": usage, "gpu_id": gpu_id})
            except Exception as e:
                logger.error(f"Error in GPU critical hook: {e}")
    
    def get_system_memory_usage(self) -> float:
        """
        Get current system memory usage as a fraction (0.0-1.0)
        
        Returns:
            Memory usage fraction
        """
        try:
            return psutil.virtual_memory().percent / 100.0
        except Exception as e:
            logger.error(f"Error getting system memory usage: {e}")
            return 0.0
    
    def get_gpu_memory_usage(self, device=0) -> float:
        """
        Get current GPU memory usage as a fraction (0.0-1.0)
        
        Args:
            device: GPU device ID
            
        Returns:
            Memory usage fraction
        """
        if HAS_TORCH and CUDA_AVAILABLE:
            try:
                # Try PyTorch's CUDA functions first
                torch.cuda.synchronize()
                allocated = torch.cuda.memory_allocated(device)
                total = torch.cuda.get_device_properties(device).total_memory
                return allocated / total
            except Exception as e:
                logger.warning(f"Error getting GPU memory via PyTorch: {e}")
                
                # Fall back to NVML
                if not self.nvml_initialized:
                    return 0.0
                    
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(device)
                    info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    return info.used / info.total
                except Exception as e:
                    logger.error(f"Error getting GPU memory via NVML: {e}")
                    return 0.0
                    
        return 0.0
    
    def get_memory_info(self) -> Dict[str, Any]:
        """
        Get detailed memory information
        
        Returns:
            Dictionary with memory information
        """
        info = {
            "ram": {},
            "swap": {},
            "gpu": {},
            "process": {}
        }
        
        # Get RAM info
        try:
            vm = psutil.virtual_memory()
            info["ram"] = {
                "total": vm.total,
                "available": vm.available,
                "used": vm.used,
                "free": vm.free,
                "percent": vm.percent
            }
        except Exception as e:
            logger.error(f"Error getting RAM info: {e}")
        
        # Get swap info
        try:
            swap = psutil.swap_memory()
            info["swap"] = {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percent": swap.percent
            }
        except Exception as e:
            logger.error(f"Error getting swap info: {e}")
        
        # Get GPU info
        if HAS_TORCH and CUDA_AVAILABLE:
            try:
                device_count = torch.cuda.device_count()
                for i in range(device_count):
                    info["gpu"][f"device_{i}"] = {
                        "name": torch.cuda.get_device_name(i),
                        "total": torch.cuda.get_device_properties(i).total_memory,
                        "allocated": torch.cuda.memory_allocated(i),
                        "reserved": torch.cuda.memory_reserved(i),
                        "percent": self.get_gpu_memory_usage(i) * 100
                    }
            except Exception as e:
                logger.error(f"Error getting GPU info: {e}")
        
        # Get process info
        try:
            process = psutil.Process()
            info["process"] = {
                "pid": process.pid,
                "memory_info": process.memory_info()._asdict(),
                "memory_percent": process.memory_percent(),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads()
            }
        except Exception as e:
            logger.error(f"Error getting process info: {e}")
        
        return info
    
    def memory_dump(self, tag: str = "manual") -> Optional[str]:
        """
        Create a memory dump for debugging
        
        Args:
            tag: Tag to identify this dump
            
        Returns:
            Path to dump file or None if dump failed
        """
        if not self.memory_dump_enabled:
            return None
            
        # Check if enough time has passed since last dump
        current_time = time.time()
        if current_time - self.last_dump_time < self.min_dump_interval:
            logger.info(f"Skipping memory dump, minimum interval not reached")
            return None
            
        self.last_dump_time = current_time
        
        # Create dump directory if it doesn't exist
        if not os.path.exists(self.memory_dump_dir):
            os.makedirs(self.memory_dump_dir, exist_ok=True)
        
        # Create unique filename based on timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.memory_dump_dir, f"memory_dump_{tag}_{timestamp}.json")
        
        try:
            # Get memory information
            memory_info = self.get_memory_info()
            
            # Add timestamp
            memory_info["timestamp"] = timestamp
            memory_info["tag"] = tag
            
            # Add Python object counts
            try:
                from collections import Counter
                import types
                
                # Get object counts
                types_count = Counter()
                for obj in gc.get_objects():
                    types_count[type(obj).__name__] += 1
                
                # Add top object types
                memory_info["python_objects"] = {
                    t: c for t, c in types_count.most_common(50)
                }
                
                # Flag large lists and dicts
                large_objects = []
                for obj in gc.get_objects():
                    if isinstance(obj, (list, tuple)):
                        try:
                            if len(obj) > 10000:
                                large_objects.append({
                                    "type": type(obj).__name__,
                                    "length": len(obj),
                                    "address": id(obj)
                                })
                        except:
                            pass
                    elif isinstance(obj, dict):
                        try:
                            if len(obj) > 10000:
                                large_objects.append({
                                    "type": "dict",
                                    "length": len(obj),
                                    "address": id(obj)
                                })
                        except:
                            pass
                memory_info["large_objects"] = large_objects[:100]  # Limit to top 100
                
            except Exception as e:
                logger.error(f"Error counting Python objects: {e}")
            
            # Add PyTorch tensor information if available
            if HAS_TORCH:
                try:
                    from utils.model_memory_tracker import ModelMemoryTracker
                    memory_info["torch"] = {
                        "version": torch.__version__,
                        "cuda_available": CUDA_AVAILABLE,
                        "cuda_device_count": torch.cuda.device_count() if CUDA_AVAILABLE else 0
                    }
                    
                    # Get tensor count
                    tensor_count = 0
                    tensor_memory = 0
                    cuda_tensor_count = 0
                    cuda_tensor_memory = 0
                    
                    for obj in gc.get_objects():
                        try:
                            if torch.is_tensor(obj):
                                tensor_count += 1
                                tensor_memory += obj.element_size() * obj.nelement()
                                
                                if obj.device.type == "cuda":
                                    cuda_tensor_count += 1
                                    cuda_tensor_memory += obj.element_size() * obj.nelement()
                        except:
                            pass
                    
                    memory_info["torch"]["tensors"] = {
                        "count": tensor_count,
                        "memory": tensor_memory,
                        "cuda_count": cuda_tensor_count,
                        "cuda_memory": cuda_tensor_memory
                    }
                    
                except Exception as e:
                    logger.error(f"Error collecting PyTorch info: {e}")
            
            # Write to file
            with open(filename, 'w') as f:
                json.dump(memory_info, f, indent=2)
            
            logger.info(f"Created memory dump: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error creating memory dump: {e}")
            return None
    
    def set_warning_hook(self, hook: Callable[[Dict[str, Any]], None]):
        """
        Set a function to be called when memory usage reaches warning threshold
        
        Args:
            hook: Function that takes a dict with warning info
        """
        self.warning_hook = hook
    
    def set_critical_hook(self, hook: Callable[[Dict[str, Any]], None]):
        """
        Set a function to be called when memory usage reaches critical threshold
        
        Args:
            hook: Function that takes a dict with critical info
        """
        self.critical_hook = hook
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure memory manager from dictionary
        
        Args:
            config: Configuration dictionary
        """
        # Update thresholds
        if "ram_warning_threshold" in config:
            self.ram_warning_threshold = config["ram_warning_threshold"] / 100.0
        
        if "ram_critical_threshold" in config:
            self.ram_critical_threshold = config["ram_critical_threshold"] / 100.0
        
        if "gpu_warning_threshold" in config:
            self.gpu_warning_threshold = config["gpu_warning_threshold"] / 100.0
        
        if "gpu_critical_threshold" in config:
            self.gpu_critical_threshold = config["gpu_critical_threshold"] / 100.0
        
        # Update check interval
        if "check_interval" in config:
            self.check_interval = config["check_interval"]
        
        # Update memory dump settings
        if "memory_dump_enabled" in config:
            self.memory_dump_enabled = config["memory_dump_enabled"]
        
        if "memory_dump_dir" in config:
            self.memory_dump_dir = config["memory_dump_dir"]
    
    def cleanup(self) -> None:
        """Clean up resources"""
        self.stop_monitoring()
        
        # Shutdown NVML if initialized
        if self.nvml_initialized:
            try:
                pynvml.nvmlShutdown()
            except Exception as e:
                logger.error(f"Error shutting down NVML: {e}")

# Global instance for easier access
_memory_manager = MemoryManager()

def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance"""
    global _memory_manager
    return _memory_manager

def setup_memory_protection(warning_hook=None, critical_hook=None) -> None:
    """
    Set up memory protection with the global memory manager
    
    Args:
        warning_hook: Function to call when memory usage reaches warning threshold
        critical_hook: Function to call when memory usage reaches critical threshold
    """
    memory_manager = get_memory_manager()
    
    # Set hooks if provided
    if warning_hook:
        memory_manager.set_warning_hook(warning_hook)
    
    if critical_hook:
        memory_manager.set_critical_hook(critical_hook)
    
    # Start monitoring
    memory_manager.start_monitoring()

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    print("Memory Manager Test")
    
    # Get memory manager
    memory_manager = get_memory_manager()
    
    # Configure from settings
    memory_manager.configure({
        "ram_warning_threshold": 80,
        "ram_critical_threshold": 90,
        "gpu_warning_threshold": 80,
        "gpu_critical_threshold": 90,
        "check_interval": 1.0,
        "memory_dump_enabled": True
    })
    
    # Set up hooks
    def warning_hook(data):
        if "ram_usage" in data:
            print(f"WARNING: RAM usage at {data['ram_usage']*100:.1f}%")
        elif "gpu_usage" in data:
            print(f"WARNING: GPU {data.get('gpu_id', 0)} usage at {data['gpu_usage']*100:.1f}%")
    
    def critical_hook(data):
        if "ram_usage" in data:
            print(f"CRITICAL: RAM usage at {data['ram_usage']*100:.1f}%!")
        elif "gpu_usage" in data:
            print(f"CRITICAL: GPU {data.get('gpu_id', 0)} usage at {data['gpu_usage']*100:.1f}%!")
    
    memory_manager.set_warning_hook(warning_hook)
    memory_manager.set_critical_hook(critical_hook)
    
    # Start monitoring
    memory_manager.start_monitoring()
    
    # Print current memory usage
    ram_usage = memory_manager.get_system_memory_usage()
    gpu_usage = memory_manager.get_gpu_memory_usage()
    
    print(f"Current RAM usage: {ram_usage*100:.1f}%")
    print(f"Current GPU usage: {gpu_usage*100:.1f}%")
    
    # Create memory dump
    dump_path = memory_manager.memory_dump("test")
    if dump_path:
        print(f"Created memory dump at: {dump_path}")
    
    # Run for a while
    try:
        for i in range(10):
            print(f"Monitoring... ({i+1}/10)")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrupted")
    finally:
        # Clean up
        memory_manager.cleanup()
