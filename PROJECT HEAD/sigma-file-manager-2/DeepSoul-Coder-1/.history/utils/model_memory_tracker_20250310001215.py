"""
Model Memory Tracker - Track memory usage of transformer models
"""
import gc
import time
import torch
import logging
import psutil
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from transformers import PreTrainedModel

from .memory_manager import get_memory_manager

logger = logging.getLogger("DeepSoul-ModelMemoryTracker")

class ModelMemoryTracker:
    """
    Track memory usage of transformer models and provide optimization techniques
    to reduce memory usage during inference and training.
    """
    
    def __init__(self, model: PreTrainedModel):
        """
        Initialize the memory tracker
        
        Args:
            model: The model to track
        """
        self.model = model
        self.memory_manager = get_memory_manager()
        self.device = next(model.parameters()).device
        self.model_name = type(model).__name__
        
        # Track per-module memory
        self.module_memory = {}
        self.param_count = {}
        self.activation_sizes = {}
        
        # Initial analysis
        self._analyze_model()
    
    def _analyze_model(self) -> None:
        """Analyze the model's memory usage by module"""
        # Count parameters
        total_params = 0
        for name, param in self.model.named_parameters():
            module_name = name.split('.')[0]
            param_size = param.nelement() * param.element_size()
            
            # Update parameter count
            if module_name not in self.param_count:
                self.param_count[module_name] = 0
            self.param_count[module_name] += param.nelement()
            
            # Update memory usage
            if module_name not in self.module_memory:
                self.module_memory[module_name] = 0
            self.module_memory[module_name] += param_size
            
            total_params += param.nelement()
            
        logger.debug(f"Model {self.model_name} has {total_params:,} parameters")
    
    def analyze_model_memory(self) -> Dict[str, Any]:
        """
        Analyze model memory usage in detail
        
        Returns:
            Dictionary with memory usage information
        """
        # Get total parameter memory
        param_memory = sum(self.module_memory.values())
        
        # Get total parameter counts
        total_params = sum(self.param_count.values())
        
        # Estimate forward/backward memory
        batch_size = 1
        seq_length = 512
        hidden_size = 768  # Default for many models, will be overridden if available
        
        # Try to extract hidden size from the model
        if hasattr(self.model, "config") and hasattr(self.model.config, "hidden_size"):
            hidden_size = self.model.config.hidden_size
        
        # Estimate activation memory (very rough approximation)
        # For transformer models, this is typically batch_size * seq_length * hidden_size * layers * 4 bytes
        num_layers = 12  # Default value
        if hasattr(self.model, "config") and hasattr(self.model.config, "num_hidden_layers"):
            num_layers = self.model.config.num_hidden_layers
        
        # Rough activation memory estimate
        activation_memory = batch_size * seq_length * hidden_size * num_layers * 4
        
        # Check current memory usage
        current_cuda_memory = 0
        if self.device.type == "cuda":
            torch.cuda.synchronize()
            current_cuda_memory = torch.cuda.memory_allocated(self.device)
        
        # Compile results
        result = {
            "model_name": self.model_name,
            "total_parameters": total_params,
            "parameter_memory_bytes": param_memory,
            "parameter_memory_mb": param_memory / (1024 * 1024),
            "estimated_activation_memory_mb": activation_memory / (1024 * 1024),
            "current_allocated_memory_mb": current_cuda_memory / (1024 * 1024),
            "device": str(self.device),
            "module_breakdown": {
                module: {
                    "parameters": self.param_count[module],
                    "memory_mb": self.module_memory[module] / (1024 * 1024)
                }
                for module in sorted(self.module_memory.keys())
            }
        }
        
        return result
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get current memory usage
        
        Returns:
            Dictionary with memory usage information
        """
        memory_info = {
            "device": str(self.device),
            "total_model_parameters": sum(self.param_count.values()),
            "total_model_memory_mb": sum(self.module_memory.values()) / (1024 * 1024)
        }
        
        # Add device-specific information
        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
            memory_info.update({
                "allocated_memory_mb": torch.cuda.memory_allocated(self.device) / (1024 * 1024),
                "reserved_memory_mb": torch.cuda.memory_reserved(self.device) / (1024 * 1024),
                "max_allocated_memory_mb": torch.cuda.max_memory_allocated(self.device) / (1024 * 1024)
            })
            
            # Calculate fragmentation
            if memory_info["reserved_memory_mb"] > 0:
                fragmentation = 1.0 - (memory_info["allocated_memory_mb"] / memory_info["reserved_memory_mb"])
                memory_info["memory_fragmentation"] = fragmentation
        
        # Add host memory info
        memory = psutil.virtual_memory()
        memory_info["host_memory_usage_percent"] = memory.percent
        memory_info["host_memory_available_gb"] = memory.available / (1024**3)
        
        return memory_info
    
    def estimate_batch_size(self, 
                          input_shape: Tuple[int, int], 
                          dtype: torch.dtype = torch.float32,
                          safety_factor: float = 0.8) -> int:
        """
        Estimate maximum batch size for given input shape
        
        Args:
            input_shape: Input shape (batch_size, sequence_length)
            dtype: Data type
            safety_factor: Safety factor to avoid OOM (0.0-1.0)
            
        Returns:
            Estimated maximum batch size
        """
        if self.device.type != "cuda":
            # For CPU, we don't estimate based on memory
            return 4  # Conservative default
        
        # Get element size for dtype
        if dtype == torch.float32:
            element_size = 4
        elif dtype == torch.float16:
            element_size = 2
        elif dtype == torch.int8:
            element_size = 1
        else:
            element_size = 4  # Default
        
        # Extract sequence length
        seq_length = input_shape[1] if len(input_shape) > 1 else 512
        
        # Estimate memory per token
        hidden_size = 768  # Default
        if hasattr(self.model, "config") and hasattr(self.model.config, "hidden_size"):
            hidden_size = self.model.config.hidden_size
        
        # Get remaining memory
        torch.cuda.synchronize(self.device)
        total_memory = torch.cuda.get_device_properties(self.device).total_memory
        allocated_memory = torch.cuda.memory_allocated(self.device)
        remaining_memory = total_memory - allocated_memory
        
        # Apply safety factor
        available_memory = remaining_memory * safety_factor
        
        # Estimate memory per example
        # This includes activations and temporary memory for attention
        num_layers = 12
        if hasattr(self.model, "config") and hasattr(self.model.config, "num_hidden_layers"):
            num_layers = self.model.config.num_hidden_layers
        
        # Memory for activations scales with sequence length
        memory_per_example = seq_length * hidden_size * element_size * num_layers * 4
        
        # Memory for attention scales with sequence length squared
        memory_per_example += seq_length * seq_length * element_size * num_layers
        
        # Calculate max batch size
        if memory_per_example > 0:
            max_batch_size = int(available_memory / memory_per_example)
            return max(1, max_batch_size)
        else:
            return 1
    
    def optimize_inference_memory(self) -> None:
        """Apply optimization techniques to reduce memory usage during inference"""
        # Check if CUDA device
        if self.device.type != "cuda":
            logger.info("Skipping memory optimization for non-CUDA device")
            return
            
        # Set the model to evaluation mode
        self.model.eval()
        
        # 1. Check if we can use half precision
        if any(p.dtype == torch.float32 for p in self.model.parameters()):
            logger.info("Converting model to half precision for memory optimization")
            self.model.half()
        
        # 2. Clean up memory
        torch.cuda.empty_cache()
        gc.collect()
        
        # 3. Optimize transformer layers if available
        self._optimize_transformer_layers()
        
        logger.info("Applied memory optimization techniques")
        
    def _optimize_transformer_layers(self) -> None:
        """Apply transformer-specific optimizations if applicable"""
        # Check if model has encoder/decoder
        has_encoder = hasattr(self.model, "encoder") and hasattr(self.model.encoder, "layers")
        has_decoder = hasattr(self.model, "decoder") and hasattr(self.model.decoder, "layers")
        has_layers = hasattr(self.model, "layers")
        
        if not (has_encoder or has_decoder or has_layers):
            return
        
        # Optimize attention layers if possible
        try:
            # Check if Flash Attention is available 
            # (requires PyTorch 2.0+ and Flash Attention to be installed)
            try:
                from torch.nn.functional import scaled_dot_product_attention
                has_sdpa = True
            except ImportError:
                has_sdpa = False
            
            if has_sdpa:
                logger.info("Using PyTorch's scaled_dot_product_attention for memory optimization")
                
                # Apply flash attention to all modules
                # This is model-specific and would need custom implementation per model type
                # Here we just log that it's available
                pass
        except Exception as e:
            logger.warning(f"Error optimizing attention layers: {e}")
    
    def print_memory_report(self) -> None:
        """Print a memory usage report to the console"""
        memory_info = self.get_memory_usage()
        
        # Header
        print("\n===== MODEL MEMORY REPORT =====")
        print(f"Model: {self.model_name}")
        print(f"Device: {memory_info['device']}")
        print(f"Total parameters: {memory_info['total_model_parameters']:,}")
        
        # Memory usage
        print("\n--- MEMORY USAGE ---")
        print(f"Model parameter memory: {memory_info['total_model_memory_mb']:.2f} MB")
        
        if self.device.type == "cuda":
            print(f"CUDA allocated memory: {memory_info['allocated_memory_mb']:.2f} MB")
            print(f"CUDA reserved memory: {memory_info['reserved_memory_mb']:.2f} MB")
            print(f"Max allocated memory: {memory_info['max_allocated_memory_mb']:.2f} MB")
            
            if "memory_fragmentation" in memory_info:
                print(f"Memory fragmentation: {memory_info['memory_fragmentation']*100:.1f}%")
        
        # Module breakdown
        print("\n--- TOP 5 MODULES BY MEMORY ---")
        module_memory = [(m, self.module_memory[m] / (1024 * 1024)) for m in self.module_memory]
        module_memory.sort(key=lambda x: x[1], reverse=True)
        
        for module, memory_mb in module_memory[:5]:
            params = self.param_count.get(module, 0)
            print(f"{module}: {memory_mb:.2f} MB ({params:,} parameters)")
        
        print("\n--- HOST MEMORY ---")
        print(f"RAM usage: {memory_info['host_memory_usage_percent']}%")
        print(f"RAM available: {memory_info['host_memory_available_gb']:.2f} GB")
        
        print("\n==============================\n")
    
    def check_input_memory(self, input_ids, attention_mask=None) -> Dict[str, float]:
        """
        Check memory requirements for inputs
        
        Args:
            input_ids: Input token IDs
            attention_mask: Attention mask (optional)
            
        Returns:
            Dictionary with memory information
        """
        result = {}
        
        # Check input_ids memory
        if hasattr(input_ids, "element_size"):
            input_size = input_ids.nelement() * input_ids.element_size()
            result["input_ids_mb"] = input_size / (1024 * 1024)
        
        # Check attention_mask memory
        if attention_mask is not None and hasattr(attention_mask, "element_size"):
            mask_size = attention_mask.nelement() * attention_mask.element_size()
            result["attention_mask_mb"] = mask_size / (1024 * 1024)
        
        # Total input size
        result["total_input_mb"] = sum(v for k, v in result.items())
        
        # Estimate KV cache size if doing generation
        if hasattr(input_ids, "shape") and len(input_ids.shape) > 1:
            batch_size, seq_len = input_ids.shape[0], input_ids.shape[1]
            
            # Get hidden dimension if available
            hidden_dim = 768  # Default
            if hasattr(self.model, "config") and hasattr(self.model.config, "hidden_size"):
                hidden_dim = self.model.config.hidden_size
            
            # Get number of layers
            num_layers = 12  # Default
            if hasattr(self.model, "config") and hasattr(self.model.config, "num_hidden_layers"):
                num_layers = self.model.config.num_hidden_layers
                
            # Estimate KV cache size (2 for K and V)
            element_size = 2 if next(self.model.parameters()).dtype == torch.float16 else 4
            kv_cache_size = batch_size * seq_len * hidden_dim * 2 * num_layers * element_size
            result["estimated_kv_cache_mb"] = kv_cache_size / (1024 * 1024)
            
        return result

def get_model_memory_usage(model: PreTrainedModel) -> str:
    """
    Get a human-readable string of model memory usage
    
    Args:
        model: Transformer model
        
    Returns:
        String with memory usage information
    """
    tracker = ModelMemoryTracker(model)
    usage = tracker.get_memory_usage()
    
    device_str = f"Device: {usage['device']}"
    param_str = f"Parameters: {usage['total_model_parameters']:,} ({usage['total_model_memory_mb']:.1f} MB)"
    
    if "allocated_memory_mb" in usage:
        memory_str = f"Memory: {usage['allocated_memory_mb']:.1f} MB allocated, {usage['reserved_memory_mb']:.1f} MB reserved"
        return f"{device_str}, {param_str}, {memory_str}"
    else:
        return f"{device_str}, {param_str}"


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Load a small model for testing
        from transformers import AutoModel
        print("Loading test model...")
        model = AutoModel.from_pretrained("distilbert-base-uncased")
        
        # Track memory usage
        tracker = ModelMemoryTracker(model)
        
        # Print memory report
        tracker.print_memory_report()
        
        # Estimate batch size
        max_batch = tracker.estimate_batch_size((1, 512))
        print(f"Estimated maximum batch size: {max_batch}")
        
        # Analyze model memory
        memory_analysis = tracker.analyze_model_memory()
        print(f"Model memory analysis: {memory_analysis['parameter_memory_mb']:.2f} MB parameters")
        
        # Optimize for inference
        tracker.optimize_inference_memory()
        print("Applied memory optimizations")
        
    except ImportError:
        print("Transformers not installed, skipping example")
    except Exception as e:
        print(f"Error in example: {e}")
