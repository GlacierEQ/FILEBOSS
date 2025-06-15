"""
Memory Diagnostics - Utilities for diagnosing and resolving memory issues
"""
import os
import gc
import sys
import time
import torch
import psutil
import logging
import threading
from pathlib import Path
from typing import Dict, List, Union, Optional, Any, Tuple
import matplotlib.pyplot as plt
import numpy as np

# Import memory manager
from .memory_manager import get_memory_manager

logger = logging.getLogger("DeepSoul-MemoryDiagnostics")

class MemoryDiagnostics:
    """Utilities for diagnosing and visualizing memory usage"""
    
    def __init__(self, output_dir: str = "memory_diagnostics"):
        """
        Initialize memory diagnostics
        
        Args:
            output_dir: Directory to store diagnostic outputs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.memory_manager = get_memory_manager()
        self.monitoring = False
        self.monitor_thread = None
        
        # Memory usage history
        self.timestamps = []
        self.ram_usage = []
        self.gpu_usage = []
        self.allocated_memory = []
    
    def start_monitoring(self, interval: float = 1.0) -> None:
        """
        Start monitoring memory usage
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self.monitoring:
            logger.warning("Monitoring already started")
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Memory monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring memory usage"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            logger.info("Memory monitoring stopped")
    
    def _monitoring_loop(self, interval: float) -> None:
        """
        Internal monitoring loop
        
        Args:
            interval: Monitoring interval in seconds
        """
        while self.monitoring:
            try:
                # Record timestamp
                self.timestamps.append(time.time())
                
                # Record RAM usage
                ram_percent = self.memory_manager.get_system_memory_usage()
                self.ram_usage.append(ram_percent)
                
                # Record GPU usage if available
                if torch.cuda.is_available():
                    gpu_percent = self.memory_manager.get_gpu_memory_usage()
                    self.gpu_usage.append(gpu_percent)
                    
                    # Record allocated memory
                    allocated = torch.cuda.memory_allocated() / (1024 * 1024)  # MB
                    self.allocated_memory.append(allocated)
            except Exception as e:
                logger.error(f"Error monitoring memory: {str(e)}")
            
            # Sleep for interval
            time.sleep(interval)
    
    def generate_report(self, include_plot: bool = True) -> str:
        """
        Generate a memory diagnostic report
        
        Args:
            include_plot: Whether to include memory usage plot
            
        Returns:
            Path to the report file
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"memory_report_{timestamp}.txt"
        
        with open(report_path, "w") as f:
            f.write("=== MEMORY DIAGNOSTIC REPORT ===\n")
            f.write(f"Generated: {timestamp}\n\n")
            
            # System info
            f.write("--- SYSTEM INFORMATION ---\n")
            f.write(f"Python version: {sys.version}\n")
            f.write(f"PyTorch version: {torch.__version__}\n")
            
            memory = psutil.virtual_memory()
            f.write(f"Total RAM: {memory.total / (1024**3):.2f} GB\n")
            f.write(f"Available RAM: {memory.available / (1024**3):.2f} GB\n")
            f.write(f"Used RAM: {memory.percent:.1f}%\n")
            
            if torch.cuda.is_available():
                f.write("\n--- GPU INFORMATION ---\n")
                f.write(f"CUDA version: {torch.version.cuda}\n")
                f.write(f"GPU count: {torch.cuda.device_count()}\n")
                
                for i in range(torch.cuda.device_count()):
                    f.write(f"\nGPU {i}: {torch.cuda.get_device_name(i)}\n")
                    total = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                    allocated = torch.cuda.memory_allocated(i) / (1024**3)
                    reserved = torch.cuda.memory_reserved(i) / (1024**3)
                    f.write(f"  Total memory: {total:.2f} GB\n")
                    f.write(f"  Allocated memory: {allocated:.2f} GB\n")
                    f.write(f"  Reserved memory: {reserved:.2f} GB\n")
                    f.write(f"  Utilization: {(allocated / total) * 100:.1f}%\n")
                    
            # Memory monitoring data
            if self.timestamps:
                f.write("\n--- MEMORY MONITORING DATA ---\n")
                duration = (self.timestamps[-1] - self.timestamps[0]) / 60  # minutes
                f.write(f"Monitoring duration: {duration:.2f} minutes\n")
                f.write(f"Data points: {len(self.timestamps)}\n")
                
                if self.ram_usage:
                    avg_ram = sum(self.ram_usage) / len(self.ram_usage)
                    max_ram = max(self.ram_usage)
                    f.write(f"Average RAM usage: {avg_ram*100:.1f}%\n")
                    f.write(f"Maximum RAM usage: {max_ram*100:.1f}%\n")
                
                if self.gpu_usage:
                    avg_gpu = sum(self.gpu_usage) / len(self.gpu_usage)
                    max_gpu = max(self.gpu_usage)
                    f.write(f"Average GPU usage: {avg_gpu*100:.1f}%\n")
                    f.write(f"Maximum GPU usage: {max_gpu*100:.1f}%\n")
                
                # Generate plot if requested
                if include_plot and len(self.timestamps) > 1:
                    plot_path = self._generate_usage_plot(timestamp)
                    f.write(f"\nMemory usage plot: {plot_path}\n")
                    
            # Memory warnings and recommendations
            f.write("\n--- RECOMMENDATIONS ---\n")
            
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated() / (1024**3)
                total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                usage_percent = allocated / total
                
                if usage_percent > 0.9:
                    f.write("! CRITICAL GPU MEMORY USAGE !\n")
                    f.write("  - Consider enabling half precision (fp16)\n")
                    f.write("  - Try reducing batch sizes\n")
                    f.write("  - Enable gradient checkpointing\n")
                    f.write("  - Use smaller model variant if possible\n")
                elif usage_percent > 0.7:
                    f.write("! HIGH GPU MEMORY USAGE !\n")
                    f.write("  - Consider using half precision\n")
                    f.write("  - Monitor batch sizes\n")
                
                # Special cases
                if allocated > 0 and torch.cuda.get_device_name(0).lower().find("3090") >= 0:
                    f.write("\nNote: RTX 3090 may need TF32 precision disabled:\n")
                    f.write("  torch.backends.cuda.matmul.allow_tf32 = False\n")
                
            # RAM recommendations
            ram_percent = memory.percent / 100
            if ram_percent > 0.9:
                f.write("\n! CRITICAL RAM USAGE !\n")
                f.write("  - Enable disk offloading for datasets\n")
                f.write("  - Reduce prefetch buffer sizes\n")
                f.write("  - Clear Python caches more aggressively\n")
            
            # Garbage collection info
            f.write("\n--- GARBAGE COLLECTION INFO ---\n")
            gc_counts = gc.get_count()
            f.write(f"Collection counts: {gc_counts}\n")
            f.write(f"Garbage collector enabled: {gc.isenabled()}\n")
            f.write(f"Thresholds: {gc.get_threshold()}\n")
        
        logger.info(f"Generated memory diagnostic report: {report_path}")
        return str(report_path)
    
    def _generate_usage_plot(self, timestamp: str) -> str:
        """
        Generate a memory usage plot
        
        Args:
            timestamp: Timestamp for the plot file
            
        Returns:
            Path to the plot
        """
        plot_path = self.output_dir / f"memory_plot_{timestamp}.png"
        
        # Convert timestamps to relative minutes
        minutes = [(t - self.timestamps[0]) / 60 for t in self.timestamps]
        
        plt.figure(figsize=(12, 6))
        
        # Plot RAM usage
        plt.plot(minutes, [x*100 for x in self.ram_usage], label="RAM Usage (%)", color="blue")
        
        # Plot GPU usage if available
        if self.gpu_usage:
            plt.plot(minutes, [x*100 for x in self.gpu_usage], label="GPU Memory Usage (%)", color="red")
        
        # Plot allocated memory if available
        if self.allocated_memory:
            # Use secondary y-axis for allocated memory in MB
            ax2 = plt.gca().twinx()
            ax2.plot(minutes, self.allocated_memory, label="Allocated GPU Memory (MB)", 
                     color="green", linestyle="--")
            ax2.set_ylabel("Memory (MB)")
            ax2.legend(loc="upper right")
        
        plt.xlabel("Time (minutes)")
        plt.ylabel("Usage (%)")
        plt.title("Memory Usage Over Time")
        plt.grid(True, alpha=0.3)
        plt.legend(loc="upper left")
        
        # Add warning threshold line
        plt.axhline(y=85, color='orange', linestyle='--', alpha=0.7)
        plt.text(minutes[-1]*0.01, 86, "Warning Threshold (85%)", color='orange')
        
        # Add critical threshold line
        plt.axhline(y=95, color='red', linestyle='--', alpha=0.7)
        plt.text(minutes[-1]*0.01, 96, "Critical Threshold (95%)", color='red')
        
        plt.savefig(plot_path)
        plt.close()
        
        return str(plot_path)

    def find_memory_leaks(self, iterations: int = 5, operation: callable = None) -> Dict[str, Any]:
        """
        Find potential memory leaks by running an operation multiple times
        
        Args:
            iterations: Number of iterations to run
            operation: Function to run each iteration (or None for default)
            
        Returns:
            Dictionary with memory leak analysis
        """
        if operation is None:
            # Default test operation - allocate and free a tensor
            operation = lambda: torch.zeros((1000, 1000), device="cuda" if torch.cuda.is_available() else "cpu")
        
        # Run garbage collection before starting
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
        
        # Measure initial memory
        initial_ram = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)  # MB
        if torch.cuda.is_available():
            initial_gpu = torch.cuda.memory_allocated() / (1024 * 1024)  # MB
        else:
            initial_gpu = 0
        
        # Track memory usage over iterations
        ram_usage = []
        gpu_usage = []
        
        # Run iterations
        for i in range(iterations):
            logger.info(f"Running leak detection iteration {i+1}/{iterations}")
            
            # Run the operation
            result = operation()
            
            # Force release the result
            del result
            
            # Run garbage collection
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Measure memory
            ram = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)  # MB
            ram_usage.append(ram)
            
            if torch.cuda.is_available():
                gpu = torch.cuda.memory_allocated() / (1024 * 1024)  # MB
                gpu_usage.append(gpu)
            else:
                gpu_usage.append(0)
        
        # Check for consistent growth in memory usage
        ram_leak = all(ram_usage[i] > ram_usage[i-1] for i in range(1, len(ram_usage)))
        gpu_leak = all(gpu_usage[i] > gpu_usage[i-1] for i in range(1, len(gpu_usage)))
        
        # Calculate growth rates
        if len(ram_usage) > 1:
            ram_growth = (ram_usage[-1] - ram_usage[0]) / (iterations - 1)
        else:
            ram_growth = 0
            
        if len(gpu_usage) > 1:
            gpu_growth = (gpu_usage[-1] - gpu_usage[0]) / (iterations - 1)
        else:
            gpu_growth = 0
        
        return {
            "iterations": iterations,
            "initial_ram_mb": initial_ram,
            "final_ram_mb": ram_usage[-1] if ram_usage else None,
            "ram_growth_per_iteration_mb": ram_growth,
            "initial_gpu_mb": initial_gpu,
            "final_gpu_mb": gpu_usage[-1] if gpu_usage else None,
            "gpu_growth_per_iteration_mb": gpu_growth,
            "potential_ram_leak": ram_leak and ram_growth > 1.0,  # More than 1MB growth per iteration
            "potential_gpu_leak": gpu_leak and gpu_growth > 1.0,
            "ram_usage_trend_mb": ram_usage,
            "gpu_usage_trend_mb": gpu_usage,
        }
    
    def find_large_tensors(self, min_size_mb: float = 10.0, show_top: int = 20) -> List[Dict[str, Any]]:
        """
        Find large tensors in memory
        
        Args:
            min_size_mb: Minimum tensor size in MB to include
            show_top: Maximum number of tensors to return
            
        Returns:
            List of large tensor information
        """
        min_size_bytes = min_size_mb * (1024 * 1024)
        large_tensors = []
        
        # Iterate through all objects in memory
        for obj in gc.get_objects():
            try:
                if torch.is_tensor(obj) and obj.size().numel() * obj.element_size() >= min_size_bytes:
                    # Collect information about the tensor
                    size_bytes = obj.size().numel() * obj.element_size()
                    tensor_info = {
                        "shape": tuple(obj.size()),
                        "dtype": str(obj.dtype),
                        "device": str(obj.device),
                        "size_mb": size_bytes / (1024 * 1024),
                        "requires_grad": obj.requires_grad
                    }
                    large_tensors.append(tensor_info)
            except Exception:
                # Skip objects that can't be processed safely
                pass
        
        # Sort by size (largest first)
        large_tensors.sort(key=lambda x: x["size_mb"], reverse=True)
        
        return large_tensors[:show_top]
    
    def snapshot_memory_state(self) -> Dict[str, Any]:
        """
        Take a snapshot of current memory state
        
        Returns:
            Dictionary with memory state information
        """
        snapshot = {
            "timestamp": time.time(),
            "ram": {},
            "gpu": {},
            "process": {}
        }
        
        # System RAM
        memory = psutil.virtual_memory()
        snapshot["ram"] = {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "used_gb": memory.used / (1024**3),
            "percent": memory.percent,
        }
        
        # GPU memory
        if torch.cuda.is_available():
            snapshot["gpu"] = {}
            for i in range(torch.cuda.device_count()):
                torch.cuda.synchronize(i)
                total = torch.cuda.get_device_properties(i).total_memory
                allocated = torch.cuda.memory_allocated(i)
                reserved = torch.cuda.memory_reserved(i)
                
                snapshot["gpu"][f"device_{i}"] = {
                    "name": torch.cuda.get_device_name(i),
                    "total_gb": total / (1024**3),
                    "allocated_gb": allocated / (1024**3),
                    "reserved_gb": reserved / (1024**3),
                    "percent": (allocated / total) * 100
                }
        
        # Process information
        process = psutil.Process(os.getpid())
        snapshot["process"] = {
            "memory_rss_gb": process.memory_info().rss / (1024**3),
            "memory_vms_gb": process.memory_info().vms / (1024**3),
            "cpu_percent": process.cpu_percent(),
            "threads": process.num_threads()
        }
        
        # Python memory info
        snapshot["python"] = {
            "gc_enabled": gc.isenabled(),
            "gc_counts": gc.get_count(),
            "gc_threshold": gc.get_threshold()
        }
        
        return snapshot
    
    def compare_snapshots(self, snapshot1: Dict[str, Any], snapshot2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two memory snapshots to identify changes
        
        Args:
            snapshot1: First snapshot
            snapshot2: Second snapshot
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            "time_elapsed_sec": snapshot2["timestamp"] - snapshot1["timestamp"],
            "ram_change_gb": snapshot2["ram"]["used_gb"] - snapshot1["ram"]["used_gb"],
            "ram_percent_change": snapshot2["ram"]["percent"] - snapshot1["ram"]["percent"],
            "process_memory_change_gb": snapshot2["process"]["memory_rss_gb"] - snapshot1["process"]["memory_rss_gb"]
        }
        
        # GPU changes
        if "gpu" in snapshot1 and "gpu" in snapshot2:
            comparison["gpu_changes"] = {}
            for device_key in snapshot1["gpu"]:
                if device_key in snapshot2["gpu"]:
                    allocated_change = snapshot2["gpu"][device_key]["allocated_gb"] - snapshot1["gpu"][device_key]["allocated_gb"]
                    percent_change = snapshot2["gpu"][device_key]["percent"] - snapshot1["gpu"][device_key]["percent"]
                    
                    comparison["gpu_changes"][device_key] = {
                        "allocated_change_gb": allocated_change,
                        "percent_change": percent_change
                    }
        
        return comparison

def measure_operation_memory(operation: callable, iterations: int = 1, warmup: int = 1) -> Dict[str, Any]:
    """
    Measure memory usage of an operation
    
    Args:
        operation: Function to measure
        iterations: Number of iterations to run
        warmup: Number of warmup iterations
        
    Returns:
        Dictionary with memory usage information
    """
    diagnostics = MemoryDiagnostics()
    
    # Run warmup iterations
    for _ in range(warmup):
        result = operation()
        del result
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    
    # Take initial snapshot
    initial_snapshot = diagnostics.snapshot_memory_state()
    
    # Reset CUDA peak stats if available
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    
    # Run operation
    start_time = time.time()
    for _ in range(iterations):
        result = operation()
    execution_time = time.time() - start_time
    
    # Take final snapshot
    final_snapshot = diagnostics.snapshot_memory_state()
    
    # Get peak stats
    peak_stats = {}
    if torch.cuda.is_available():
        peak_stats["peak_gpu_memory_gb"] = torch.cuda.max_memory_allocated() / (1024**3)
    
    # Compare snapshots
    comparison = diagnostics.compare_snapshots(initial_snapshot, final_snapshot)
    
    # Build results
    result = {
        "iterations": iterations,
        "execution_time_sec": execution_time,
        "time_per_iteration_sec": execution_time / iterations,
        "memory_change": comparison,
        "peak_stats": peak_stats,
        "initial_state": initial_snapshot,
        "final_state": final_snapshot
    }
    
    return result

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    print("=== Memory Diagnostics Tool ===")
    diagnostics = MemoryDiagnostics()
    
    # Start monitoring
    print("Starting memory monitoring...")
    diagnostics.start_monitoring(interval=0.5)
    
    # Simulate some memory-intensive operations
    print("Simulating memory operations...")
    tensors = []
    for i in range(5):
        tensor = torch.zeros((1000, 1000), device="cuda" if torch.cuda.is_available() else "cpu")
        tensors.append(tensor)
        print(f"Created tensor {i+1}, sleeping...")
        time.sleep(1)
    
    # Create a memory report
    print("Generating memory report...")
    report_path = diagnostics.generate_report()
    print(f"Report generated: {report_path}")
    
    # Find large tensors
    print("\nFinding large tensors...")
    large_tensors = diagnostics.find_large_tensors(min_size_mb=1.0)
    for i, tensor in enumerate(large_tensors):
        print(f"{i+1}. Shape: {tensor['shape']}, Size: {tensor['size_mb']:.2f} MB, Device: {tensor['device']}")
    
    # Clean up
    diagnostics.stop_monitoring()
    del tensors
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    print("\nDiagnostics completed!")
