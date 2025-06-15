"""
Memory-Efficient Batch Processor - Utilities for processing large datasets with memory constraints
"""
import os
import gc
import json
import torch
import logging
import numpy as np
from typing import Dict, List, Optional, Union, Any, Generator, Callable, Tuple, Iterable
from pathlib import Path
import tempfile

from .memory_manager import get_memory_manager
from implementation.oom_protected_execution import oom_protected, MemoryEfficientContext, adaptive_batch_size

logger = logging.getLogger("DeepSoul-BatchProcessor")

class MemoryEfficientBatchProcessor:
    """
    Process large datasets in memory-efficient batches with automatic disk offloading when needed
    """
    
    def __init__(self, 
                initial_batch_size: int = 16, 
                min_batch_size: int = 1,
                max_batch_size: int = 256,
                use_disk_offload: bool = True,
                keep_tensors_on_cpu: bool = True):
        """
        Initialize the memory-efficient batch processor
        
        Args:
            initial_batch_size: Starting batch size to try
            min_batch_size: Minimum acceptable batch size
            max_batch_size: Maximum batch size to try
            use_disk_offload: Whether to offload data to disk when memory is low
            keep_tensors_on_cpu: Whether to keep tensors on CPU when not in use
        """
        self.initial_batch_size = initial_batch_size
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.use_disk_offload = use_disk_offload
        self.keep_tensors_on_cpu = keep_tensors_on_cpu
        self.memory_manager = get_memory_manager()
        
        # Create temp directory for disk offloading
        self.temp_dir = Path(tempfile.gettempdir()) / "deepsoul_batch_offload"
        if use_disk_offload:
            self.temp_dir.mkdir(exist_ok=True)
    
    def process_dataset(self, 
                       dataset: List[Any], 
                       process_func: Callable[[List[Any]], Any], 
                       postprocess_func: Optional[Callable[[Any], Any]] = None,
                       progress_callback: Optional[Callable[[int, int], None]] = None) -> List[Any]:
        """
        Process a dataset with memory-efficient batching
        
        Args:
            dataset: The dataset to process
            process_func: Function to process a single batch
            postprocess_func: Optional function to post-process each batch result
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of processed results
        """
        results = []
        
        # Start with initial batch size
        current_batch_size = self.initial_batch_size
        
        # Track processing status
        total_items = len(dataset)
        processed_items = 0
        
        while processed_items < total_items:
            remaining_items = total_items - processed_items
            # Don't make a batch larger than remaining items
            batch_size = min(current_batch_size, remaining_items)
            batch_data = dataset[processed_items:processed_items+batch_size]
            
            try:
                # Process batch with memory protection
                with MemoryEfficientContext():
                    batch_result = process_func(batch_data)
                
                # Post-process if needed
                if postprocess_func:
                    batch_result = postprocess_func(batch_result)
                
                # Store results (offload to disk if needed and enabled)
                if self.use_disk_offload and self.memory_manager.get_system_memory_usage() > 0.85:
                    batch_result = self._offload_to_disk(batch_result, f"batch_{processed_items}")
                
                results.append(batch_result)
                processed_items += batch_size
                
                # Update progress if callback provided
                if progress_callback:
                    progress_callback(processed_items, total_items)
                
                # Try increasing batch size if we're well below the max
                if batch_size == current_batch_size and current_batch_size < self.max_batch_size:
                    # Check memory usage before increasing
                    if (torch.cuda.is_available() and 
                        self.memory_manager.get_gpu_memory_usage() < 0.6 and
                        self.memory_manager.get_system_memory_usage() < 0.7):
                        new_batch_size = min(current_batch_size * 2, self.max_batch_size)
                        logger.info(f"Increasing batch size: {current_batch_size} -> {new_batch_size}")
                        current_batch_size = new_batch_size
                
            except RuntimeError as e:
                # Check if error is CUDA OOM
                if "CUDA out of memory" in str(e) and batch_size > self.min_batch_size:
                    prev_batch_size = batch_size
                    # Decrease batch size
                    current_batch_size = max(self.min_batch_size, batch_size // 2)
                    logger.warning(f"CUDA OOM detected. Reducing batch size: {prev_batch_size} -> {current_batch_size}")
                    
                    # Clear memory
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    gc.collect()
                    
                    # Don't advance processed_items counter so we retry this batch
                else:
                    # Not an OOM error or already at minimum batch size
                    logger.error(f"Error processing batch: {str(e)}")
                    raise
        
        # Cleanup temp files
        if self.use_disk_offload:
            self._cleanup_temp_files()
            
        # Load results from disk if needed
        results = [self._load_from_disk(r) if isinstance(r, str) else r for r in results]
        
        return results
    
    def generate_batches(self, 
                        dataset: List[Any], 
                        batch_size: Optional[int] = None) -> Generator[List[Any], None, None]:
        """
        Generate memory-efficient batches from dataset
        
        Args:
            dataset: Dataset to batch
            batch_size: Batch size (if None, automatically determined)
            
        Yields:
            Batches of data
        """
        if batch_size is None:
            batch_size = self.initial_batch_size
        
        # Check dataset size
        total_items = len(dataset)
        position = 0
        
        while position < total_items:
            remaining = total_items - position
            current_batch_size = min(batch_size, remaining)
            
            yield dataset[position:position+current_batch_size]
            position += current_batch_size
    
    def adaptive_batch_processing(self, 
                                process_func: Callable[[List[Any], int], Any],
                                dataset: List[Any]) -> List[Any]:
        """
        Process a dataset with adaptive batch size based on available memory
        
        Args:
            process_func: Function taking (data, batch_size) as arguments
            dataset: Dataset to process
            
        Returns:
            Processed results
        """
        @adaptive_batch_size(self.initial_batch_size, self.min_batch_size, self.max_batch_size)
        def batch_processor(data, batch_size):
            return process_func(data, batch_size)
            
        return batch_processor(dataset)
    
    def _offload_to_disk(self, data: Any, identifier: str) -> str:
        """
        Offload data to disk to save memory
        
        Args:
            data: Data to offload
            identifier: Unique identifier for this data
            
        Returns:
            Path to the offloaded data
        """
        if not self.use_disk_offload:
            return data
            
        filename = f"{identifier}_{os.getpid()}.pt"
        file_path = self.temp_dir / filename
        
        if torch.is_tensor(data) or isinstance(data, dict) and any(torch.is_tensor(v) for v in data.values()):
            # Tensor data
            if self.keep_tensors_on_cpu:
                # Move tensors to CPU before saving
                if torch.is_tensor(data) and data.device.type == "cuda":
                    data = data.cpu()
                elif isinstance(data, dict):
                    for key, value in data.items():
                        if torch.is_tensor(value) and value.device.type == "cuda":
                            data[key] = value.cpu()
            
            torch.save(data, file_path)
        else:
            # Regular Python data
            with open(file_path, 'w') as f:
                json.dump(data, f)
        
        logger.debug(f"Offloaded data to {file_path}")
        return str(file_path)
    
    def _load_from_disk(self, file_path: str) -> Any:
        """
        Load data from disk
        
        Args:
            file_path: Path to the offloaded data
            
        Returns:
            The loaded data
        """
        if not isinstance(file_path, str) or not os.path.exists(file_path):
            return file_path
            
        path = Path(file_path)
        
        if path.suffix == '.pt':
            # PyTorch data
            data = torch.load(path)
        else:
            # Regular Python data
            with open(path, 'r') as f:
                data = json.load(f)
        
        logger.debug(f"Loaded data from {file_path}")
        return data
    
    def _cleanup_temp_files(self) -> None:
        """Clean up temporary files"""
        if not self.use_disk_offload:
            return
            
        for file_path in self.temp_dir.glob(f"*_{os.getpid()}.pt"):
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {file_path}: {str(e)}")

class DynamicBatchSizeScheduler:
    """
    Dynamic batch size scheduler for memory-efficient dataset processing
    """
    
    def __init__(self, 
                initial_batch_size: int = 16, 
                min_batch_size: int = 1,
                max_batch_size: int = 256,
                growth_rate: float = 1.5,
                shrink_rate: float = 0.5,
                target_memory_usage: float = 0.7):
        """
        Initialize the batch size scheduler
        
        Args:
            initial_batch_size: Starting batch size
            min_batch_size: Minimum batch size
            max_batch_size: Maximum batch size
            growth_rate: Factor to grow batch size by when memory is available
            shrink_rate: Factor to shrink batch size by when OOM occurs
            target_memory_usage: Target memory usage (0.0-1.0)
        """
        self.batch_size = initial_batch_size
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.growth_rate = growth_rate
        self.shrink_rate = shrink_rate
        self.target_memory_usage = target_memory_usage
        self.memory_manager = get_memory_manager()
        
        # History tracking
        self.oom_count = 0
        self.success_count = 0
    
    def get_next_batch_size(self) -> int:
        """
        Get the next batch size based on current memory conditions
        
        Returns:
            Next batch size to try
        """
        # Check current memory usage
        if torch.cuda.is_available():
            gpu_usage = self.memory_manager.get_gpu_memory_usage()
            
            # If GPU usage is low, consider increasing batch size
            if gpu_usage < self.target_memory_usage * 0.8 and self.success_count >= 2:
                self._increase_batch_size()
                self.success_count = 0
        
        return self.batch_size
    
    def update_after_success(self) -> None:
        """Update scheduler after successful batch processing"""
        self.success_count += 1
    
    def update_after_oom(self) -> int:
        """
        Update scheduler after OOM error
        
        Returns:
            New batch size to try
        """
        self.oom_count += 1
        self.success_count = 0
        
        old_batch_size = self.batch_size
        self._decrease_batch_size()
        
        logger.warning(f"OOM detected. Reducing batch size: {old_batch_size} → {self.batch_size}")
        
        # Clear memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        
        return self.batch_size
    
    def _increase_batch_size(self) -> None:
        """Increase batch size according to growth rate"""
        new_size = min(int(self.batch_size * self.growth_rate), self.max_batch_size)
        if new_size > self.batch_size:
            logger.debug(f"Increasing batch size: {self.batch_size} → {new_size}")
            self.batch_size = new_size
    
    def _decrease_batch_size(self) -> None:
        """Decrease batch size according to shrink rate"""
        new_size = max(int(self.batch_size * self.shrink_rate), self.min_batch_size)
        self.batch_size = new_size
