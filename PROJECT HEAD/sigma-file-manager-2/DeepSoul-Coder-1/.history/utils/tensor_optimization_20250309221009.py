"""
Tensor Optimization - Utilities for optimizing tensor operations to reduce memory usage
"""
import gc
import torch
import logging
from typing import Dict, List, Optional, Union, Any, Tuple, Callable

from .memory_manager import get_memory_manager

logger = logging.getLogger("DeepSoul-TensorOptimization")

class TensorOptimizer:
    """Utilities for optimizing tensor operations to reduce memory usage"""
    
    def __init__(self, device: Optional[torch.device] = None):
        """
        Initialize the tensor optimizer
        
        Args:
            device: Target device for optimized tensors
        """
        self.device = device or (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))
        self.memory_manager = get_memory_manager()
        
        # Maps from torch datatypes to more efficient ones for specific operations
        self.dtype_optimization_map = {
            torch.float32: torch.float16 if device and device.type == "cuda" else torch.float32,
            torch.float64: torch.float32,
            torch.int64: torch.int32
        }
    
    def optimize_dtype(self, tensor: torch.Tensor) -> torch.Tensor:
        """
        Optimize tensor dtype based on its content and target device
        
        Args:
            tensor: Input tensor
            
        Returns:
            Optimized tensor
        """
        original_dtype = tensor.dtype
        
        # Only optimize if we have a mapping for this dtype
        if original_dtype in self.dtype_optimization_map:
            target_dtype = self.dtype_optimization_map[original_dtype]
            
            # Special handling for int64 -> int32 conversion
            if original_dtype == torch.int64 and target_dtype == torch.int32:
                # Check for value range to ensure we don't lose data
                if tensor.min() >= torch.iinfo(torch.int32).min and tensor.max() <= torch.iinfo(torch.int32).max:
                    return tensor.to(target_dtype)
                return tensor
            
            # For float types on GPU, always prefer fp16 where possible
            if original_dtype == torch.float32 and tensor.device.type == "cuda":
                return tensor.half()  # Convert to float16
                
            # General case
            return tensor.to(target_dtype)
        
        return tensor
    
    def optimize_batch_size(self, batch_tensor_factory: Callable[[int], torch.Tensor], 
                          min_batch: int = 1, max_batch: int = 128) -> int:
        """
        Find optimal batch size that fits in memory
        
        Args:
            batch_tensor_factory: Function that creates a batch tensor of given size
            min_batch: Minimum acceptable batch size
            max_batch: Maximum batch size to try
            
        Returns:
            Optimal batch size
        """
        # Start with max_batch and reduce until it fits
        current_batch = max_batch
        
        while current_batch >= min_batch:
            try:
                # Try to create tensor with current batch size
                tensor = batch_tensor_factory(current_batch)
                
                # If we got here, it worked
                # Clean up to avoid accumulating tensors
                del tensor
                if self.device.type == "cuda":
                    torch.cuda.empty_cache()
                
                # Return this batch size with a small safety margin
                safety_factor = 0.9  # 10% safety margin
                safe_batch = max(min_batch, int(current_batch * safety_factor))
                return safe_batch
                
            except RuntimeError as e:
                if "CUDA out of memory" in str(e) or "DefaultCPUAllocator: can't allocate memory" in str(e):
                    # Reduce batch size and try again
                    previous_batch = current_batch
                    current_batch = max(min_batch, current_batch // 2)
                    logger.info(f"Reducing batch size from {previous_batch} to {current_batch}")
                    
                    # Clear memory for next try
                    gc.collect()
                    if self.device.type == "cuda":
                        torch.cuda.empty_cache()
                    
                    if current_batch == min_batch and previous_batch == min_batch:
                        # Already at minimum and still OOM
                        logger.error("Cannot fit even minimum batch size in memory")
                        return 0
                else:
                    # Not an OOM error
                    raise
        
        return min_batch
    
    def optimize_inplace(self, tensor: torch.Tensor) -> torch.Tensor:
        """
        Optimize tensor in-place if possible
        
        Args:
            tensor: Input tensor
            
        Returns:
            Optimized tensor (same object if optimized in-place)
        """
        # Check if detached leaf tensor with no gradients needed
        if not tensor.requires_grad and tensor.is_leaf:
            # Check data types that could be optimized
            if tensor.dtype == torch.float32 and tensor.device.type == "cuda":
                tensor.data = tensor.data.half()  # In-place conversion to float16
            
            # For int64 -> int32, we need to be careful about value range
            elif tensor.dtype == torch.int64:
                if tensor.min() >= torch.iinfo(torch.int32).min and tensor.max() <= torch.iinfo(torch.int32).max:
                    tensor.data = tensor.data.to(torch.int32)
        
        return tensor
    
    def shard_large_tensor(self, tensor: torch.Tensor, 
                         max_shard_size_mb: float = 200.0) -> List[torch.Tensor]:
        """
        Shard a large tensor into smaller pieces to fit in memory
        
        Args:
            tensor: Large tensor to shard
            max_shard_size_mb: Maximum shard size in MB
            
        Returns:
            List of tensor shards
        """
        # Calculate total size and how many shards needed
        tensor_size_bytes = tensor.numel() * tensor.element_size()
        tensor_size_mb = tensor_size_bytes / (1024 * 1024)
        
        # If tensor is small enough, return it directly
        if tensor_size_mb <= max_shard_size_mb:
            return [tensor]
        
        # Calculate number of shards needed
        num_shards = int(torch.ceil(torch.tensor(tensor_size_mb / max_shard_size_mb)).item())
        
        # Determine which dimension to split on
        split_dim = 0
        for i, dim_size in enumerate(tensor.shape):
            if dim_size > num_shards:
                split_dim = i
                break
        
        # Split tensor into shards
        shards = torch.tensor_split(tensor, num_shards, dim=split_dim)
        logger.info(f"Split tensor of size {tensor_size_mb:.2f} MB into {len(shards)} shards")
        
        return shards
    
    def process_batched(self, data: torch.Tensor, process_fn: Callable, 
                      batch_size: Optional[int] = None,
                      dim: int = 0) -> torch.Tensor:
        """
        Process a large tensor in batches to avoid OOM
        
        Args:
            data: Input tensor
            process_fn: Function to process each batch
            batch_size: Batch size (if None, automatically determined)
            dim: Dimension to batch on
            
        Returns:
            Processed tensor
        """
        # Handle empty tensor
        if data.numel() == 0:
            return data
            
        # Get data length along batch dimension
        data_len = data.shape[dim]
        
        # Auto-determine batch size if not specified
        if batch_size is None:
            # Start with reasonable default
            if self.device.type == "cuda":
                # Different defaults based on available GPU memory
                total_gpu_memory = torch.cuda.get_device_properties(self.device).total_memory
                if total_gpu_memory >= 16 * (1024**3):  # 16GB+ VRAM
                    batch_size = 32
                elif total_gpu_memory >= 8 * (1024**3):  # 8GB+ VRAM
                    batch_size = 16
                else:
                    batch_size = 8
            else:
                batch_size = 64  # Larger batches on CPU
                
            # Dynamically adjust based on tensor size
            element_size = data.element_size()
            element_count = data.numel() // data_len
            bytes_per_item = element_size * element_count
            
            # Adjust batch size to target around 500MB per batch
            target_batch_bytes = 500 * (1024**2)  # 500MB
            memory_based_batch = max(1, int(target_batch_bytes / bytes_per_item))
            batch_size = min(batch_size, memory_based_batch)
            
            logger.debug(f"Auto-selected batch size: {batch_size}")
        
        # Process in batches and concatenate results
        results = []
        
        for i in range(0, data_len, batch_size):
            # Create batch slice
            batch_end = min(i + batch_size, data_len)
            indices = [slice(None)] * data.ndim
            indices[dim] = slice(i, batch_end)
            batch = data[indices]
            
            # Process batch
            with torch.no_grad():  # No gradients for efficiency
                batch_result = process_fn(batch)
                
            # Add to results
            results.append(batch_result)
            
            # Clean up to prevent OOM
            if self.device.type == "cuda" and i % (batch_size * 4) == 0:
                torch.cuda.empty_cache()
        
        # Concatenate results along the same dimension
        try:
            return torch.cat(results, dim=dim)
        except RuntimeError as e:
            # If concatenation fails (maybe inconsistent shapes), return list
            logger.warning(f"Could not concatenate results: {str(e)}")
            return results
    
    def mixed_precision_inference(self, model: torch.nn.Module, 
                               inputs: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Run model inference with automatic mixed precision for memory efficiency
        
        Args:
            model: PyTorch model
            inputs: Model inputs
            
        Returns:
            Model outputs
        """
        # Check if we're on CUDA
        if self.device.type != "cuda":
            # No mixed precision for CPU
            with torch.no_grad():
                return model(**inputs)
        
        # Convert inputs to half precision
        half_inputs = {k: v.half() if v.dtype == torch.float32 else v for k, v in inputs.items()}
        
        # Run model with autocast
        try:
            from torch.cuda.amp import autocast
            with torch.no_grad(), autocast():
                outputs = model(**half_inputs)
            return outputs
        except ImportError:
            # Autocast not available, use manual half precision
            if next(model.parameters()).dtype != torch.float16:
                model = model.half()
            
            with torch.no_grad():
                outputs = model(**half_inputs)
            return outputs
    
    def quantize_tensor(self, tensor: torch.Tensor, bits: int = 8) -> torch.Tensor:
        """
        Quantize a tensor to a lower bit precision
        
        Args:
            tensor: Input tensor
            bits: Target bit depth (8 or 4)
            
        Returns:
            Quantized tensor
        """
        if bits not in [4, 8]:
            raise ValueError("Only 4 and 8 bit quantization supported")
            
        if bits == 8:
            # Simple quantization to int8
            if tensor.dtype != torch.float32:
                tensor = tensor.float()
                
            # Find min and max values
            min_val = tensor.min()
            max_val = tensor.max()
            
            # Scale to [0, 255]
            scale = 255.0 / (max_val - min_val + 1e-10)
            zero_point = -min_val * scale
            
            # Quantize
            quantized = torch.clamp((tensor * scale + zero_point).round(), 0, 255).byte()
            
            # Store quantization parameters for dequantization
            quantized.scale = scale
            quantized.zero_point = zero_point
            
            return quantized
        else:
            # For 4-bit, we pack two 4-bit values into one int8 value
            # This is simplified - a real implementation would be more complex
            if tensor.dtype != torch.float32:
                tensor = tensor.float()
                
            # Scale to [0, 15]
            min_val = tensor.min()
            max_val = tensor.max()
            scale = 15.0 / (max_val - min_val + 1e-10)
            zero_point = -min_val * scale
            
            # Quantize to 4 bits [0, 15]
            tensor_4bit = torch.clamp((tensor * scale + zero_point).round(), 0, 15).byte()
            
            # Pack two 4-bit values into one byte
            packed_shape = list(tensor_4bit.shape)
            if packed_shape[-1] % 2 != 0:
                # Pad with zeros if needed
                padding = torch.zeros((*packed_shape[:-1], 1), dtype=torch.uint8, device=tensor.device)
                tensor_4bit = torch.cat([tensor_4bit, padding], dim=-1)
                packed_shape[-1] += 1
                
            packed_shape[-1] //= 2
            packed = torch.zeros(packed_shape, dtype=torch.uint8, device=tensor.device)
            
            # Pack with bit shifting
            even_elements = tensor_4bit[..., ::2]
            odd_elements = tensor_4bit[..., 1::2]
            packed = (even_elements << 4) | odd_elements
            
            # Store quantization parameters for dequantization
            packed.scale = scale
            packed.zero_point = zero_point
            packed.bits = 4
            
            return packed
    
    def dequantize_tensor(self, quantized: torch.Tensor) -> torch.Tensor:
        """
        Dequantize a tensor back to floating point
        
        Args:
            quantized: Quantized tensor with scale and zero_point attributes
            
        Returns:
            Dequantized tensor
        """
        if not hasattr(quantized, 'scale') or not hasattr(quantized, 'zero_point'):
            raise ValueError("Tensor doesn't have quantization parameters")
            
        scale = quantized.scale
        zero_point = quantized.zero_point
        
        # Check if we have 4-bit packed tensor
        if hasattr(quantized, 'bits') and quantized.bits == 4:
            # Unpack 4-bit values
            unpacked_shape = list(quantized.shape)
            unpacked_shape[-1] *= 2
            
            unpacked = torch.zeros(unpacked_shape, dtype=torch.uint8, device=quantized.device)
            unpacked[..., ::2] = (quantized >> 4) & 0x0F  # Extract high 4 bits
            unpacked[..., 1::2] = quantized & 0x0F  # Extract low 4 bits
            
            # Dequantize
            dequantized = ((unpacked.float() - zero_point) / scale)
            return dequantized
        
        # Regular 8-bit dequantization
        dequantized = ((quantized.float() - zero_point) / scale)
        return dequantized

# Convenience function for quick tensor optimization
def optimize_tensor(tensor: torch.Tensor, device: Optional[torch.device] = None) -> torch.Tensor:
    """
    Optimize a tensor for memory efficiency
    
    Args:
        tensor: Tensor to optimize
        device: Optional target device
    
    Returns:
        Optimized tensor
    """
    optimizer = TensorOptimizer(device)
    return optimizer.optimize_dtype(tensor)
