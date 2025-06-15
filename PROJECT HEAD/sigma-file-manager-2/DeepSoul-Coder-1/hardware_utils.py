"""
Utility functions for hardware detection and optimization in DeepSeek-Coder
"""
import os
import platform
import json
import torch
from pathlib import Path

class HardwareManager:
    """Class to detect and manage hardware accelerators for DeepSeek-Coder"""
    
    def __init__(self):
        self.device_priority = os.environ.get("DEEPSEEK_DEVICE_PRIORITY", "auto").lower()
        self.env_file = Path("environment_info.json")
        self.env_info = self._load_environment_info()
        self.available_devices = self._detect_devices()
    
    def _load_environment_info(self):
        """Load environment info from file if available"""
        if self.env_file.exists():
            try:
                with open(self.env_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _detect_devices(self):
        """Detect available AI acceleration devices"""
        devices = {
            "cpu": {"available": True, "name": "CPU", "memory_gb": 0, "priority": 0}
        }
        
        # Check for CUDA GPU
        if torch.cuda.is_available():
            cuda_devices = []
            for i in range(torch.cuda.device_count()):
                name = torch.cuda.get_device_name(i)
                memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                cuda_devices.append({"index": i, "name": name, "memory_gb": memory})
            
            devices["cuda"] = {
                "available": True,
                "name": "NVIDIA GPU",
                "devices": cuda_devices,
                "priority": 100
            }
        
        # Check for Apple MPS (Metal Performance Shaders)
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            devices["mps"] = {
                "available": True,
                "name": "Apple Neural Engine",
                "priority": 90
            }
        
        # Check for AMD ROCm
        try:
            if hasattr(torch.version, "hip") and torch.version.hip is not None:
                devices["rocm"] = {
                    "available": True,
                    "name": "AMD ROCm",
                    "priority": 80
                }
        except:
            pass
        
        # Check for DirectML
        try:
            import torch_directml
            devices["directml"] = {
                "available": True,
                "name": "DirectML",
                "priority": 70
            }
        except ImportError:
            pass
        
        # Check for OpenVINO
        try:
            import openvino
            devices["openvino"] = {
                "available": True,
                "name": "OpenVINO",
                "priority": 60
            }
        except ImportError:
            pass
        
        return devices
    
    def get_optimal_device(self):
        """Get the optimal device for DeepSeek-Coder based on priority and settings"""
        if self.device_priority == "cpu":
            return "cpu"
        
        # If user specified a device
        for device_type in ["cuda", "mps", "rocm", "directml", "openvino"]:
            if self.device_priority == device_type and device_type in self.available_devices and self.available_devices[device_type]["available"]:
                return device_type
        
        # Auto detect the best device
        available = [(k, v["priority"]) for k, v in self.available_devices.items() if v["available"]]
        if not available:
            return "cpu"
        
        # Sort by priority (higher is better)
        available.sort(key=lambda x: x[1], reverse=True)
        return available[0][0]
    
    def get_torch_device(self):
        """Get the appropriate torch.device object"""
        device_type = self.get_optimal_device()
        
        if device_type == "cuda":
            return torch.device("cuda")
        elif device_type == "mps":
            return torch.device("mps")
        elif device_type == "rocm":
            return torch.device("cuda")  # ROCm uses CUDA API
        elif device_type == "directml":
            import torch_directml
            return torch_directml.device()
        else:
            return torch.device("cpu")
    
    def get_optimal_dtype(self):
        """Get the optimal dtype for the detected hardware"""
        device_type = self.get_optimal_device()
        
        if device_type == "cpu":
            return torch.float32
        elif device_type == "cuda":
            if torch.cuda.is_bf16_supported():
                return torch.bfloat16
            else:
                return torch.float16
        elif device_type == "mps":
            return torch.float16
        else:
            return torch.float32
    
    def print_hardware_info(self):
        """Print information about available AI acceleration hardware"""
        print("\n=== AI Acceleration Hardware ===")
        
        optimal = self.get_optimal_device()
        for name, info in self.available_devices.items():
            if info["available"]:
                is_optimal = "(SELECTED)" if name == optimal else ""
                print(f"- {info['name']} {is_optimal}")
                
                # Print GPU details if available
                if name == "cuda" and "devices" in info:
                    for i, gpu in enumerate(info["devices"]):
                        print(f"  GPU {i}: {gpu['name']} ({gpu['memory_gb']:.2f} GB)")
        
        print(f"\nOptimal device: {self.available_devices[optimal]['name']}")
        print(f"Optimal precision: {self.get_optimal_dtype()}")
        print("=" * 30)


# Simple test function when run directly
if __name__ == "__main__":
    hw = HardwareManager()
    hw.print_hardware_info()
