"""
Model Memory Tracker - Track memory usage of transformer models
"""
import gc
import torch
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
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
        Initialize the model memory tracker
        
        Args:
            model: Transformer model to track
        """
        self.model = model
        self.memory_manager = get_memory_manager()
        self.layer_memory_usage: Dict[str, int] = {}
        self.total_params = 0
        self.param_memory = 0
        
        # Initialize with memory analysis
        self.analyze_model_memory()
    
    def analyze_model_memory(self) -> Dict[str, Any]:
        """
        Analyze the memory usage of the model
        
        Returns:
            Dictionary with memory analysis results
        """
        # Get model device
        device = next(self.model.parameters()).device
        
        # Capture memory before analysis
        if device.type == "cuda":
            torch.cuda.synchronize(device)
            mem_before = torch.cuda.memory_allocated(device)
        
        # Analyze parameters
        total_params = 0
        param_size = 0
        buffer_size = 0
        
        for name, param in self.model.named_parameters():
            param_count = np.prod(param.shape)
            total_params += param_count
            param_size += param_count * param.element_size()
            
            # Track memory usage by layer
            layer_name = name.split('.')[0] if '.' in name else 'other'
            if layer_name not in self.layer_memory_usage:
                self.layer_memory_usage[layer_name] = 0
            self.layer_memory_usage[layer_name] += param_count * param.element_size()
        
        # Add buffer memory
        for name, buffer in self.model.named_buffers():
            buffer_size += np.prod(buffer.shape) * buffer.element_size()
        
        # Estimate activation memory (rough estimate)
        batch_size = 1
        seq_length = 512
        hidden_size = getattr(self.model.config, 'hidden_size', 768)
        num_layers = getattr(self.model.config, 'num_hidden_layers', 12)
        
        # Estimate forward activation memory
        activation_size = batch_size * seq_length * hidden_size * 4  # float32
        activation_size *= num_layers  # Account for all layers
        
        # Calculate total memory
        total_memory = param_size + buffer_size
        
        # Capture memory after analysis
        if device.type == "cuda":
            torch.cuda.synchronize(device)
            mem_after = torch.cuda.memory_allocated(device)
            overhead = mem_after - mem_before - total_memory
        else:
            overhead = 0
        
        # Store results
        self.total_params = total_params
        self.param_memory = param_size
        
        # Return memory analysis
        return {
            "total_parameters": total_params,
            "parameter_memory": param_size,
            "buffer_memory": buffer_size,
            "estimated_activation_memory": activation_size,
            "total_model_memory": total_memory,
            "overhead": overhead,
            "layer_memory": self.layer_memory_usage,
        }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get current memory usage of the model
        
        Returns:
            Dictionary with memory usage information
        """
        device = next(self.model.parameters()).device
        result = {
            "device": str(device),
            "total_parameters": self.total_params,
            "parameter_memory_mb": self.param_memory / (1024 * 1024)
        }
        
        if device.type == "cuda":
            torch.cuda.synchronize(device)
            result["gpu_allocated_mb"] = torch.cuda.memory_allocated(device) / (1024 * 1024)
            result["gpu_reserved_mb"] = torch.cuda.memory_reserved(device) / (1024 * 1024)
            
            device_props = torch.cuda.get_device_properties(device)
            result["gpu_total_mb"] = device_props.total_memory / (1024 * 1024)
            result["gpu_name"] = device_props.name
        
        return result
    
    def estimate_batch_size(self, 
                          input_shape: Tuple[int, int], 
                          dtype: torch.dtype = torch.float32,
                          safety_factor: float = 0.8) -> int:
        """
        Estimate maximum batch size that will fit in memory
        
        Args:
            input_shape: Shape of single input (sequence_length, feature_dim)
            dtype: Data type of inputs
            safety_factor: Safety factor (0-1) to leave memory headroom
            
        Returns:
            Maximum estimated batch size
        """
        device = next(self.model.parameters()).device
        
        if device.type != "cuda":
            # For CPU, we're less constrained
            return 32  # Default conservative value
        
        # Get current available memory
        torch.cuda.synchronize(device)
        total_memory = torch.cuda.get_device_properties(device).total_memory
        allocated_memory = torch.cuda.memory_allocated(device)
        available_memory = (total_memory - allocated_memory) * safety_factor
        
        # Get memory required for model if it's not loaded yet
        model_memory = self.param_memory
        
        # Estimate memory for single item
        seq_len, feat_dim = input_shape
        element_size = {
            torch.float32: 4,
            torch.float16: 2,
            torch.int64: 8,
            torch.int32: 4,
            torch.int16: 2,
            torch.int8: 1
        }.get(dtype, 4)
        
        # Estimate memory per sequence considering activations
        # Assumes transformer architecture with attention
        hidden_size = getattr(self.model.config, 'hidden_size', 768)
        num_layers = getattr(self.model.config, 'num_hidden_layers', 12)
        
        # Memory for inputs
        input_memory = seq_len * feat_dim * element_size
        
        # Memory for transformer activations (key, query, value, output projections)
        # This is a simplification - actual memory usage depends on architecture details
        activation_memory = seq_len * hidden_size * 4 * element_size * num_layers * 2  # *2 for forward and backward pass
        
        # Memory for attention matrix
        attention_memory = seq_len * seq_len * 4  # float32 typically used for attention
        
        # Memory per sequence
        memory_per_sequence = input_memory + activation_memory + attention_memory
        
        # Calculate max batch size
        max_batch_size = int(available_memory / memory_per_sequence)
        
        # Sanity check to avoid unreasonable values
        max_batch_size = max(1, min(max_batch_size, 512))  # Cap at 512 as a reasonable upper limit
        
        return max_batch_size
    
    def optimize_inference_memory(self) -> None:
        """Optimize model for inference to reduce memory usage"""
        device = next(self.model.parameters()).device
        
        # 1. Set to eval mode
        self.model.eval()
        
        # 2. Use mixed precision if on CUDA
        if device.type == "cuda":
            # Check if model is already in half precision
            is_half = next(self.model.parameters()).dtype == torch.float16
            
            if not is_half:
                logger.info("Converting model to half precision for memory efficiency")
                self.model = self.model.half()
        
        # 3. Run garbage collection
        gc.collect()
        if device.type == "cuda":
            torch.cuda.empty_cache()
    
    def print_memory_report(self) -> None:
        """Print detailed memory report for the model"""
        analysis = self.analyze_model_memory()
        usage = self.get_memory_usage()
        
        # Convert to MB for readability
        param_memory_mb = analysis["parameter_memory"] / (1024 * 1024)
        buffer_memory_mb = analysis["buffer_memory"] / (1024 * 1024)
        activation_memory_mb = analysis["estimated_activation_memory"] / (1024 * 1024)
        total_memory_mb = analysis["total_model_memory"] / (1024 * 1024)
        
        print(f"\n===== Model Memory Report =====")
        print(f"Model type: {type(self.model).__name__}")
        print(f"Device: {usage['device']}")
        print(f"Total parameters: {analysis['total_parameters']:,}")
        print(f"Parameter memory: {param_memory_mb:.2f} MB")
        print(f"Buffer memory: {buffer_memory_mb:.2f} MB")
        print(f"Estimated activation memory: {activation_memory_mb:.2f} MB")
        print(f"Total model memory: {total_memory_mb:.2f} MB")
        
        if "gpu_allocated_mb" in usage:
            print(f"\nGPU: {usage['gpu_name']}")
            print(f"GPU memory allocated: {usage['gpu_allocated_mb']:.2f} MB")
            print(f"GPU memory reserved: {usage['gpu_reserved_mb']:.2f} MB")
            print(f"GPU total memory: {usage['gpu_total_mb']:.2f} MB")
            print(f"GPU memory utilization: {(usage['gpu_allocated_mb'] / usage['gpu_total_mb']) * 100:.1f}%")
        
        print("\nMemory by layer:")
        sorted_layers = sorted(analysis['layer_memory'].items(), key=lambda x: x[1], reverse=True)
        for layer_name, memory in sorted_layers[:10]:  # Top 10 layers
            print(f"  {layer_name}: {memory / (1024 * 1024):.2f} MB")
        
        if len(sorted_layers) > 10:
            print(f"  ... and {len(sorted_layers) - 10} more layers")
        
        print("\nBatch size estimation:")
        for seq_len in [128, 512, 1024, 2048]:
            batch_size = self.estimate_batch_size((seq_len, 768))
            print(f"  Sequence length {seq_len}: ~{batch_size} sequences per batch")
            
        print("===============================")
    
    def check_input_memory(self, input_ids, attention_mask=None) -> Dict[str, float]:
        """
        Check memory usage of input tensors
        
        Args:
            input_ids: Input token IDs tensor
            attention_mask: Attention mask tensor
            
        Returns:
            Dictionary with memory usage in MB
        """
        memory_usage = {}
        
        # Input IDs memory
        input_memory = input_ids.element_size() * input_ids.nelement()
        memory_usage["input_ids_mb"] = input_memory / (1024 * 1024)
        
        # Attention mask memory
        if attention_mask is not None:
            mask_memory = attention_mask.element_size() * attention_mask.nelement()
            memory_usage["attention_mask_mb"] = mask_memory / (1024 * 1024)
        
        # Total input memory
        total_memory = input_memory
        if attention_mask is not None:
            total_memory += mask_memory
        
        memory_usage["total_input_mb"] = total_memory / (1024 * 1024)
        
        return memory_usage

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
    param_str = f"Parameters: {usage['total_parameters']:,} ({usage['parameter_memory_mb']:.1f} MB)"
    
    if "gpu_allocated_mb" in usage:
        gpu_str = f"GPU memory: {usage['gpu_allocated_mb']:.1f} MB / {usage['gpu_total_mb']:.1f} MB ({(usage['gpu_allocated_mb'] / usage['gpu_total_mb']) * 100:.1f}%)"
        return f"{device_str}, {param_str}, {gpu_str}"
    else:
        return f"{device_str}, {param_str}"

if __name__ == "__main__":
    # Example usage
    from transformers import AutoModel
    
    logging.basicConfig(level=logging.INFO)
    
    print("Loading model...")
    model_name = "gpt2"  # Small model for testing
    model = AutoModel.from_pretrained(model_name)
    
    print("Tracking memory usage...")
    tracker = ModelMemoryTracker(model)
    
    # Print memory report
    tracker.print_memory_report()
    
    # Optimize for inference
    print("\nOptimizing model for inference...")
    tracker.optimize_inference_memory()
    
    # Print memory report after optimization
    tracker.print_memory_report()
