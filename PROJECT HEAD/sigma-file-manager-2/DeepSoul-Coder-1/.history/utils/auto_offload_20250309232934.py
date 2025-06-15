"""
Auto Offload - Automatic offloading of model parameters to CPU/disk to reduce memory usage
"""
import os
import gc
import torch
import logging
import tempfile
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

from .memory_manager import get_memory_manager

logger = logging.getLogger("DeepSoul-AutoOffload")

class AutoOffload:
    """
    Automatically offload model parameters to CPU/disk to reduce GPU memory usage
    
    This class helps manage large models by dynamically moving portions of a model
    between GPU and CPU based on memory constraints and usage patterns.
    """
    
    def __init__(self, device: str = "cuda", threshold: float = 0.85, enable_disk_offload: bool = False):
        """
        Initialize auto offload manager
        
        Args:
            device: Target device for model execution
            threshold: Memory threshold (0.0-1.0) that triggers offloading
            enable_disk_offload: Whether to offload to disk when CPU memory is also constrained
        """
        self.device = torch.device(device) if torch.cuda.is_available() else torch.device("cpu")
        self.cpu_device = torch.device("cpu")
        self.threshold = threshold
        self.enable_disk_offload = enable_disk_offload
        self.memory_manager = get_memory_manager()
        
        # Create temp directory for disk offloading
        if enable_disk_offload:
            self.temp_dir = Path(tempfile.gettempdir()) / "deepsoul_offload"
            self.temp_dir.mkdir(exist_ok=True)
        
        # Tracking parameters
        self.offloaded_params = {}
        self.param_usage_count = {}
    
    def check_memory_pressure(self) -> bool:
        """
        Check if system is under memory pressure
        
        Returns:
            True if memory is constrained, False otherwise
        """
        if self.device.type == "cuda":
            return self.memory_manager.get_gpu_memory_usage() > self.threshold
        else:
            return self.memory_manager.get_system_memory_usage() > self.threshold
    
    def offload_parameters(self, model: torch.nn.Module, layer_indices: Optional[List[int]] = None) -> None:
        """
        Offload model parameters to CPU or disk
        
        Args:
            model: PyTorch model to offload parameters from
            layer_indices: Specific layer indices to offload (if None, auto-select)
        """
        # Only offload if using CUDA and under memory pressure
        if self.device.type != "cuda" or not torch.cuda.is_available():
            return
        
        # Check memory pressure
        if not self.check_memory_pressure():
            return
        
        logger.info("Offloading model parameters to reduce memory usage")
        
        # Determine which layers to offload
        if layer_indices is None:
            # Auto-select layers based on usage count
            if hasattr(model, "layers") or hasattr(model, "encoder") or hasattr(model, "decoder"):
                # Look for transformer-like models
                if hasattr(model, "layers"):
                    num_layers = len(model.layers)
                    targets = model.layers
                elif hasattr(model, "encoder") and hasattr(model.encoder, "layers"):
                    num_layers = len(model.encoder.layers)
                    targets = model.encoder.layers
                elif hasattr(model, "decoder") and hasattr(model.decoder, "layers"):
                    num_layers = len(model.decoder.layers)
                    targets = model.decoder.layers
                else:
                    logger.warning("Could not determine model layers automatically")
                    return
                
                # Offload lower layers first (typically less frequently used)
                layer_indices = list(range(min(4, num_layers)))
                logger.info(f"Auto-selected {len(layer_indices)} layers for offloading")
            else:
                # Could not determine layers, skip offloading
                logger.warning("Could not determine model structure for auto-offloading")
                return
        
        # Get layers to offload
        if hasattr(model, "layers"):
            layers = [model.layers[i] for i in layer_indices if i < len(model.layers)]
        elif hasattr(model, "encoder") and hasattr(model.encoder, "layers"):
            layers = [model.encoder.layers[i] for i in layer_indices if i < len(model.encoder.layers)]
        elif hasattr(model, "decoder") and hasattr(model.decoder, "layers"):
            layers = [model.decoder.layers[i] for i in layer_indices if i < len(model.decoder.layers)]
        else:
            logger.warning("Model structure not supported for offloading")
            return
        
        # Offload parameters
        for i, layer in enumerate(layers):
            layer_name = f"layer_{layer_indices[i]}"
            
            # Store original parameters
            self.offloaded_params[layer_name] = {}
            
            # Move parameters to CPU
            for name, param in layer.named_parameters():
                param_key = f"{layer_name}.{name}"
                # Only offload if parameter is on target device
                if param.device == self.device:
                    # Save reference to parameter data
                    self.offloaded_params[layer_name][name] = param.data
                    
                    # Move to CPU
                    param.data = param.data.to(self.cpu_device)
                    
                    # Record usage count
                    if param_key not in self.param_usage_count:
                        self.param_usage_count[param_key] = 0
        
        # Force garbage collection
        gc.collect()
        torch.cuda.empty_cache()
        
        logger.info(f"Offloaded {len(layers)} layers to CPU")
    
    def prefetch_parameters(self, model: torch.nn.Module, layer_indices: List[int]) -> None:
        """
        Prefetch parameters back to target device
        
        Args:
            model: PyTorch model
            layer_indices: Layer indices to prefetch
        """
        if self.device.type != "cuda":
            return
        
        # Get layers to prefetch
        if hasattr(model, "layers"):
            layers = [model.layers[i] for i in layer_indices if i < len(model.layers)]
        elif hasattr(model, "encoder") and hasattr(model.encoder, "layers"):
            layers = [model.encoder.layers[i] for i in layer_indices if i < len(model.encoder.layers)]
        elif hasattr(model, "decoder") and hasattr(model.decoder, "layers"):
            layers = [model.decoder.layers[i] for i in layer_indices if i < len(model.decoder.layers)]
        else:
            return
        
        # Prefetch parameters
        prefetched_count = 0
        for i, layer in enumerate(layers):
            layer_name = f"layer_{layer_indices[i]}"
            
            if layer_name in self.offloaded_params:
                for name, param in layer.named_parameters():
                    if name in self.offloaded_params[layer_name]:
                        # Update usage count
                        param_key = f"{layer_name}.{name}"
                        self.param_usage_count[param_key] = self.param_usage_count.get(param_key, 0) + 1
                        
                        # Skip if memory is under pressure
                        if self.check_memory_pressure():
                            continue
                        
                        # Move back to target device
                        param.data = param.data.to(self.device)
                        prefetched_count += 1
        
        logger.debug(f"Prefetched {prefetched_count} parameters to {self.device}")
    
    def offload_entire_model(self, model: torch.nn.Module) -> None:
        """
        Offload the entire model to CPU
        
        Args:
            model: PyTorch model to offload
        """
        logger.info("Offloading entire model to CPU")
        model.to(self.cpu_device)
        gc.collect()
        torch.cuda.empty_cache()
    
    def disk_offload_tensors(self, tensors: Dict[str, torch.Tensor]) -> Dict[str, str]:
        """
        Offload tensors to disk
        
        Args:
            tensors: Dictionary of tensors to offload
            
        Returns:
            Dictionary mapping tensor names to file paths
        """
        if not self.enable_disk_offload:
            logger.warning("Disk offloading is not enabled")
            return {}
            
        file_paths = {}
        for name, tensor in tensors.items():
            # Create a unique filename
            file_path = self.temp_dir / f"{name}_{id(tensor)}.pt"
            
            # Save tensor to disk
            torch.save(tensor, file_path)
            
            # Record file path
            file_paths[name] = str(file_path)
            
            # Delete tensor
            del tensor
            
        # Force garbage collection
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        return file_paths
    
    def load_disk_tensors(self, file_paths: Dict[str, str]) -> Dict[str, torch.Tensor]:
        """
        Load tensors from disk
        
        Args:
            file_paths: Dictionary mapping tensor names to file paths
            
        Returns:
            Dictionary of loaded tensors
        """
        tensors = {}
        for name, file_path in file_paths.items():
            # Load tensor from disk
            tensor = torch.load(file_path)
            
            # Store in dictionary
            tensors[name] = tensor
            
            # Delete file to free space
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Could not delete temporary file {file_path}: {str(e)}")
                
        return tensors
    
    def optimize_memory_usage(self, model: torch.nn.Module) -> None:
        """
        Optimize memory usage based on current memory state
        
        Args:
            model: PyTorch model to optimize
        """
        # Check if we're using CUDA
        if self.device.type != "cuda":
            return
            
        # Get current memory usage
        gpu_usage = self.memory_manager.get_gpu_memory_usage()
        
        if gpu_usage > self.threshold:
            # Memory pressure is high, offload parameters
            self.offload_parameters(model)
        elif gpu_usage < 0.5:
            # Memory pressure is low, consider prefetching frequent layers
            most_used_layers = self._get_most_used_layers(3)
            if most_used_layers:
                self.prefetch_parameters(model, most_used_layers)
    
    def _get_most_used_layers(self, count: int = 3) -> List[int]:
        """
        Get the most frequently used layers
        
        Args:
            count: Number of layer indices to return
            
        Returns:
            List of layer indices
        """
        # Group param usage by layer
        layer_usage = {}
        for param_key, usage_count in self.param_usage_count.items():
            layer_name = param_key.split('.')[0]
            layer_id = int(layer_name.split('_')[1])
            
            if layer_id not in layer_usage:
                layer_usage[layer_id] = 0
            layer_usage[layer_id] += usage_count
        
        # Get top layers by usage
        if not layer_usage:
            return []
            
        sorted_layers = sorted(layer_usage.items(), key=lambda x: x[1], reverse=True)
        return [layer_id for layer_id, _ in sorted_layers[:count]]
    
    def cleanup(self) -> None:
        """Clean up temporary files"""
        if self.enable_disk_offload:
            # Delete all temporary files
            for file_path in self.temp_dir.glob("*.pt"):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Could not delete temporary file {file_path}: {str(e)}")
            
            # Try to remove the directory
            try:
                self.temp_dir.rmdir()
            except Exception:
                # Directory may not be empty, which is fine
                pass

# Global instance for easy access
_auto_offload = AutoOffload()

def get_auto_offload() -> AutoOffload:
    """Get the global auto offload instance"""
    global _auto_offload
    return _auto_offload

def setup_auto_offload(device: str = "cuda", threshold: float = 0.85, enable_disk_offload: bool = False) -> AutoOffload:
    """
    Set up auto offload with custom settings
    
    Args:
        device: Target device for model execution
        threshold: Memory threshold that triggers offloading
        enable_disk_offload: Whether to enable disk offloading
        
    Returns:
        Configured AutoOffload instance
    """
    global _auto_offload
    _auto_offload = AutoOffload(device, threshold, enable_disk_offload)
    return _auto_offload

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Set up auto offload
    offloader = setup_auto_offload(threshold=0.8)
    
    # Test with a simple model
    try:
        from transformers import AutoModel
        model = AutoModel.from_pretrained("gpt2")
        
        # Offload parameters
        offloader.offload_parameters(model)
        
        # Prefetch parameters
        offloader.prefetch_parameters(model, [0, 1])
        
        # Optimize memory usage
        offloader.optimize_memory_usage(model)
    except ImportError:
        print("Transformers library not found, skipping model test")
