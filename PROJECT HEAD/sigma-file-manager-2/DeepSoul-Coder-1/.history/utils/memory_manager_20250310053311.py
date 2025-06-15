"""
Utility functions for managing memory usage, especially for large AI models.
"""
import os
import gc
import logging
import time
import platform
import threading
import tracemalloc
from typing import Dict, Optional, Callable, Any
import torch
from .tensor_optimization import optimize_model_memory
from .auto_offload import offload_module
from .service_manager import ServiceManager

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    A class for managing memory, including GPU memory, during AI model execution.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, service_manager: Optional[ServiceManager] = None):
        """
        Initializes the MemoryManager with optional configuration.
        """
        self.config = config if config is not None else {}
        self.service_manager = service_manager if service_manager else ServiceManager()def __init__(self, config: Optional[Dict[str, Any]] = None, service_manager: Optional[ServiceManager] = None):
        self.nvml_available = self._check_nvml_availability()
        self.lock = threading.Lock() the MemoryManager with optional configuration.
        self.peak_memory_usage = {"gpu": 0, "cpu": 0}
        self.tracemalloc_enabled = False= config if config is not None else {}
        self.tracemalloc_lock = threading.Lock()        self.service_manager = service_manager if service_manager else ServiceManager()
ability()
    def _check_nvml_availability(self) -> bool:        self.lock = threading.Lock()
        """mory_usage = {"gpu": 0, "cpu": 0}
        Checks if NVML (NVIDIA Management Library) is available. self.tracemalloc_enabled = False
        """
        try:
            import py3nvml.py3nvml as nvml
            nvml.nvmlInit()
            logger.info("NVML is available, GPU monitoring enabled.") Checks if NVML (NVIDIA Management Library) is available.
            return True    """
        except ImportError:
            logger.warning("py3nvml is not installed. GPU monitoring is disabled.")
            return False
        except Exception as e:e, GPU monitoring enabled.")
            logger.error(f"Error initializing NVML: {e}")
            return False
 installed. GPU monitoring is disabled.")
    def get_gpu_memory_usage(self) -> Dict[int, Dict[str, float]]:    return False
        """
        Retrieves GPU memory usage for each GPU.nitializing NVML: {str(e)}")
        """
        gpu_memory_usage = {}
        if self.nvml_available:get_gpu_memory_usage(self) -> Dict[int, Dict[str, float]]:
            try:
                import py3nvml.py3nvml as nvmlmory usage for each GPU.
                nvml.nvmlInit()
                device_count = nvml.nvmlDeviceGetCount()}
                for i in range(device_count):le:
                    handle = nvml.nvmlDeviceGetHandleByIndex(i)
                    mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)       import py3nvml.py3nvml as nvml
                    gpu_memory_usage[i] = {        nvml.nvmlInit()
                        "total": mem_info.total / 1024**2,  # Convert to MB nvml.nvmlDeviceGetCount()
                        "used": mem_info.used / 1024**2,ount):
                        "free": mem_info.free / 1024**2,etHandleByIndex(i)
                    }nvml.nvmlDeviceGetMemoryInfo(handle)
            except Exception as e:
                logger.error(f"Error getting GPU memory usage: {e}")                "total": mem_info.total / 1024**2,  # Convert to MB
        else:mem_info.used / 1024**2,
            logger.warning("NVML is not available, cannot retrieve GPU memory usage.")mem_info.free / 1024**2,
        return gpu_memory_usage
    except Exception as e:
    def get_cpu_memory_usage(self) -> Dict[str, float]:etting GPU memory usage: {str(e)}")
        """
        Retrieves CPU memory usage.er.warning("NVML is not available, cannot retrieve GPU memory usage.")
        """
        memory_usage = {
            "used": 0.0, -> Dict[str, float]:
            "available": 0.0,
            "percent": 0.0
        }
        try:
            import psutil        "used": 0.0,
            cpu_memory = psutil.virtual_memory()
            memory_usage["used"] = cpu_memory.used / 1024**2  # Convert to MB
            memory_usage["available"] = cpu_memory.available / 1024**2
            memory_usage["percent"] = cpu_memory.percent
        except ImportError: psutil
            logger.warning("psutil is not installed, cannot retrieve CPU memory usage.")cpu_memory = psutil.virtual_memory()
        except Exception as e:"] = cpu_memory.used / 1024**2  # Convert to MB
            logger.error(f"Error getting CPU memory usage: {e}")    memory_usage["available"] = cpu_memory.available / 1024**2
        return memory_usage] = cpu_memory.percent

    def log_memory_usage(self, prefix: str = "") -> None:not installed, cannot retrieve CPU memory usage.")
        """
        Logs the current memory usage for both CPU and GPU.r(f"Error getting CPU memory usage: {str(e)}")
        """eturn memory_usage
        cpu_memory = self.get_cpu_memory_usage()
        logger.info(f"{prefix}CPU Memory Usage: Used={cpu_memory['used']:.2f} MB, Available={cpu_memory['available']:.2f} MB, Percent={cpu_memory['percent']:.2f}%")log_memory_usage(self, prefix: str = "") -> None:

        gpu_memory = self.get_gpu_memory_usage()    Logs the current memory usage for both CPU and GPU.
        if gpu_memory:
            for gpu_id, usage in gpu_memory.items():)
                logger.info(f"{prefix}GPU {gpu_id} Memory Usage: Used={usage['used']:.2f} MB, Free={usage['free']:.2f} MB, Total={usage['total']:.2f} MB")PU Memory Usage: Used={cpu_memory['used']:.2f} MB, Available={cpu_memory['available']:.2f} MB, Percent={cpu_memory['percent']:.2f}%")
        else:
            logger.info(f"{prefix}No GPU memory information available.")memory = self.get_gpu_memory_usage()

    def clear_gpu_cache(self) -> None:    for gpu_id, usage in gpu_memory.items():
        """prefix}GPU {gpu_id} Memory Usage: Used={usage['used']:.2f} MB, Free={usage['free']:.2f} MB, Total={usage['total']:.2f} MB")
        Clears the GPU cache to free up memory.
        """logger.info(f"{prefix}No GPU memory information available.")
        if torch.cuda.is_available():
            try:def clear_gpu_cache(self) -> None:
                with self.lock:
                    torch.cuda.empty_cache()
                    logger.info("GPU cache cleared.")
            except Exception:.cuda.is_available():
                logger.error("Error clearing GPU cache.")
        else:
            logger.warning("CUDA is not available, cannot clear GPU cache.")
        logger.info("GPU cache cleared.")
    def collect_garbage(self) -> None:
        """            logger.error("Error clearing GPU cache.")
        Performs garbage collection to free up memory.
        """he.")
        with self.lock:
            gc.collect()
            logger.info("Garbage collection performed.")
Performs garbage collection to free up memory.
    def enable_tracemalloc(self) -> None:
        """
        Enables tracemalloc to track memory allocations.
        """ed.")
        with self.tracemalloc_lock:
            if not self.tracemalloc_enabled:enable_tracemalloc(self) -> None:
                tracemalloc.start()
                self.tracemalloc_enabled = Truec to track memory allocations.
                logger.info("Tracemalloc enabled.")
            else:
                logger.warning("Tracemalloc is already enabled.")

    def disable_tracemalloc(self) -> None:        self.tracemalloc_enabled = True
        """oc enabled.")
        Disables tracemalloc.
        """lready enabled.")
        with self.tracemalloc_lock:
            if self.tracemalloc_enabled:
                tracemalloc.stop()
                self.tracemalloc_enabled = False
                logger.info("Tracemalloc disabled.")
            else:
                logger.warning("Tracemalloc is not enabled.")
            tracemalloc.stop()
    def start_peak_memory_monitoring(self) -> None:= False
        """oc disabled.")
        Starts monitoring peak memory usage.
        """"Tracemalloc is not enabled.")
        self.enable_tracemalloc()
        self.peak_memory_usage = {"gpu": 0, "cpu": 0}ing(self) -> None:
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()emory usage.
        logger.info("Peak memory monitoring started.")
alloc()
    def stop_peak_memory_monitoring(self) -> Dict[str, float]:lf.peak_memory_usage = {"gpu": 0, "cpu": 0}
        """if torch.cuda.is_available():
        Stops monitoring peak memory usage and returns the results.ry_stats()
        """ory monitoring started.")
        self.disable_tracemalloc()
        if torch.cuda.is_available():float]:
            self.peak_memory_usage["gpu"] = torch.cuda.max_memory_allocated() / 1024**2
        else:lts.
            self.peak_memory_usage["gpu"] = 0.0    """

        snapshot = tracemalloc.take_snapshot()
        total_allocated = sum(stat.size for stat in snapshot.statistics('traceback'))da.max_memory_allocated() / 1024**2
        self.peak_memory_usage["cpu"] = total_allocated / 1024**2
    self.peak_memory_usage["gpu"] = 0.0
        logger.info(f"Peak memory monitoring stopped. GPU={self.peak_memory_usage['gpu']:.2f} MB, CPU={self.peak_memory_usage['cpu']:.2f} MB")
        return self.peak_memory_usagehot()
at.size for stat in snapshot.statistics('traceback'))
    def get_detailed_memory_breakdown(self, top_n: int = 10) -> None:"] = total_allocated / 1024**2
        """
        Prints a detailed breakdown of memory usage using tracemalloc.gger.info(f"Peak memory monitoring stopped. GPU={self.peak_memory_usage['gpu']:.2f} MB, CPU={self.peak_memory_usage['cpu']:.2f} MB")
        """return self.peak_memory_usage
        if not self.tracemalloc_enabled:
            logger.warning("Tracemalloc is not enabled. Enable it first to get a detailed memory breakdown.")lf, top_n: int = 10) -> None:
            return"""
n of memory usage using tracemalloc.
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('traceback')if not self.tracemalloc_enabled:
is not enabled. Enable it first to get a detailed memory breakdown.")
        logger.info(f"Top {top_n} memory allocating files:")
        for stat in top_stats[:top_n]:
            logger.info(f"  {stat.size / 1024:.1f} KB: {stat.traceback.format()}")snapshot = tracemalloc.take_snapshot()
('traceback')
    def optimize_model_memory(self, model: torch.nn.Module, optimizer: Optional[torch.optim.Optimizer] = None, level: str = "L1") -> None:
        """nfo(f"Top {top_n} memory allocating files:")
        Applies memory optimization techniques to the given model.
        """size / 1024:.1f} KB: {stat.traceback.format()}")
        optimize_model_memory(model, optimizer, level)
def optimize_model_memory(self, model: torch.nn.Module, optimizer: Optional[torch.optim.Optimizer] = None, level: str = "L1") -> None:
    def offload_module(self, module: torch.nn.Module, device: str = "cpu") -> None:
        """chniques to the given model.
        Offloads a module to the specified device (CPU or disk).
        """odel, optimizer, level)
        offload_module(module, device)
le: torch.nn.Module, device: str = "cpu") -> None:
    def is_cuda_available(self) -> bool:
        """ specified device (CPU or disk).
        Checks if CUDA is available.
        """ule, device)
        return torch.cuda.is_available()
is_cuda_available(self) -> bool:
    def get_system_info(self) -> Dict[str, Any]:
        """ilable.
        Retrieves system information, including OS and Python version.
        """
        system_info = {
            "os": platform.system(),ict[str, Any]:
            "os_release": platform.release(),
            "python_version": platform.python_version()    Retrieves system information, including OS and Python version.
        }
        return system_info

def safe_memory_allocate(size: int, device: str = "cpu") -> Optional[torch.Tensor]:rm.release(),
    """    "python_version": platform.python_version()
    Safely allocates a tensor of the specified size, handling potential OOM errors.
    """
    try:
        if device == "cuda" and torch.cuda.is_available(): device: str = "cpu") -> Optional[torch.Tensor]:
            tensor = torch.empty(size, device="cuda")
        else: allocates a tensor of the specified size, handling potential OOM errors.
            tensor = torch.empty(size, device="cpu")
        return tensor
    except Exception:da.is_available():
        logger.error(f"Failed to allocate tensor of size {size} on device {device}.")    tensor = torch.empty(size, device="cuda")
        return None
evice="cpu")
def test_memory_management():
    """pt Exception:
    A simple test function to demonstrate memory management capabilities.te tensor of size {size} on device {device}.")
    """
    memory_manager = MemoryManager()

    # Log initial memory usage
    memory_manager.log_memory_usage(prefix="Initial: ")nstrate memory management capabilities.

    # Allocate a large tensor (if possible)memory_manager = MemoryManager()
    large_tensor = safe_memory_allocate((1024, 1024, 100), device="cuda")
    if large_tensor is None:nitial memory usage
        large_tensor = safe_memory_allocate((1024, 1024, 100), device="cpu")

    if large_tensor is not None: large tensor (if possible)
        logger.info("Successfully allocated large tensor.")locate((1024, 1024, 100), device="cuda")
        memory_manager.log_memory_usage(prefix="After allocation: ")e_tensor is None:
e_tensor = safe_memory_allocate((1024, 1024, 100), device="cpu")
        # Clear GPU cache and collect garbage
        memory_manager.clear_gpu_cache()e:
        memory_manager.collect_garbage()
        memory_manager.log_memory_usage(prefix="After clearing cache: ").log_memory_usage(prefix="After allocation: ")

        # Delete the tensor
        del large_tensorory_manager.clear_gpu_cache()
        memory_manager.collect_garbage()
        logger.info("Deleted large tensor.")memory_manager.log_memory_usage(prefix="After clearing cache: ")
        memory_manager.log_memory_usage(prefix="After deletion: ")
    else:
        logger.warning("Could not allocate large tensor, skipping some tests.")large_tensor
anager.collect_garbage()
    # Test peak memory monitoringe tensor.")
    memory_manager.start_peak_memory_monitoring()ory_manager.log_memory_usage(prefix="After deletion: ")
    _ = safe_memory_allocate((512, 512, 50), device="cuda")
    peak_usage = memory_manager.stop_peak_memory_monitoring()arning("Could not allocate large tensor, skipping some tests.")
    logger.info(f"Peak memory usage: GPU={peak_usage['gpu']:.2f} MB, CPU={peak_usage['cpu']:.2f} MB")

    # Get system info
    system_info = memory_manager.get_system_info()
    logger.info(f"System Information: {system_info}")k_memory_monitoring()
e: GPU={peak_usage['gpu']:.2f} MB, CPU={peak_usage['cpu']:.2f} MB")
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) info
    test_memory_management()t_system_info()
