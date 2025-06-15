"""
Inference Scheduler - Manage and schedule memory-intensive inference tasks
"""
import os
import gc
import time
import torch
import queue
import logging
import threading
from typing import Dict, List, Any, Callable, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from pathlib import Path

from .memory_manager import get_memory_manager
from implementation.oom_protected_execution import oom_protected, MemoryEfficientContext

logger = logging.getLogger("DeepSoul-InferenceScheduler")

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass(order=True)
class InferenceTask:
    """Representation of a schedulable inference task"""
    priority: TaskPriority = field(default=TaskPriority.NORMAL)
    created_at: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: f"task_{time.time()}_{id(threading.current_thread())}")
    inputs: Dict[str, Any] = field(default_factory=dict, compare=False)
    callback: Optional[Callable[[Dict[str, Any]], None]] = field(default=None, compare=False)
    error_callback: Optional[Callable[[Exception], None]] = field(default=None, compare=False)
    timeout: Optional[float] = field(default=None)
    max_retries: int = field(default=2)
    retries: int = field(default=0)
    device_preference: str = field(default="cuda")
    
    def __post_init__(self):
        # Convert string priority to enum if needed
        if isinstance(self.priority, str):
            self.priority = TaskPriority[self.priority.upper()]

class InferenceScheduler:
    """
    Scheduler for managing and executing inference tasks efficiently
    
    This scheduler handles memory-intensive inference tasks with priorities,
    timeouts, and automatic OOM protection.
    """
    
    def __init__(self, 
                model: torch.nn.Module,
                max_workers: int = 1,
                enable_batching: bool = True,
                max_batch_size: int = 4,
                output_dir: Optional[str] = None):
        """
        Initialize the inference scheduler
        
        Args:
            model: Model to use for inference
            max_workers: Maximum number of worker threads
            enable_batching: Whether to enable automatic batching of compatible tasks
            max_batch_size: Maximum batch size for batched inference
            output_dir: Directory to store task outputs and error logs
        """
        self.model = model
        self.max_workers = max_workers
        self.enable_batching = enable_batching
        self.max_batch_size = max_batch_size
        self.output_dir = Path(output_dir) if output_dir else Path("inference_outputs")
        
        self.output_dir.mkdir(exist_ok=True)
        
        # Task queue (priority queue)
        self.task_queue = queue.PriorityQueue()
        
        # Initialize memory manager
        self.memory_manager = get_memory_manager()
        
        # Worker threads
        self.workers = []
        self.running = False
        
        # Task status tracking
        self.tasks_stats = {
            "submitted": 0,
            "completed": 0,
            "failed": 0,
            "oom_retries": 0
        }
        
        # Lock for thread safety
        self.stats_lock = threading.Lock()
        
        # Dictionary to track currently processing tasks
        self.processing_tasks = {}
        self.processing_lock = threading.Lock()
    
    def start(self) -> None:
        """Start the scheduler workers"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        self.running = True
        
        # Create and start worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"InferenceWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
            
        logger.info(f"Started {self.max_workers} inference worker threads")
    
    def stop(self) -> None:
        """Stop the scheduler and workers"""
        self.running = False
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=2.0)
            
        self.workers = []
        logger.info("Inference scheduler stopped")
    
    def submit_task(self, 
                  inputs: Dict[str, Any], 
                  callback: Optional[Callable] = None,
                  error_callback: Optional[Callable] = None,
                  priority: Union[TaskPriority, str] = TaskPriority.NORMAL,
                  timeout: Optional[float] = None,
                  device: str = "cuda") -> str:
        """
        Submit an inference task to the scheduler
        
        Args:
            inputs: Model inputs for inference
            callback: Function to call with results
            error_callback: Function to call if an error occurs
            priority: Task priority
            timeout: Maximum execution time in seconds
            device: Preferred device for execution
            
        Returns:
            Task ID
        """
        task = InferenceTask(
            priority=priority,
            inputs=inputs,
            callback=callback,
            error_callback=error_callback,
            timeout=timeout,
            device_preference=device
        )
        
        # Add to queue
        self.task_queue.put(task)
        
        # Update stats
        with self.stats_lock:
            self.tasks_stats["submitted"] += 1
            
        logger.debug(f"Task {task.id} submitted with priority {priority}")
        return task.id
    
    def _worker_loop(self) -> None:
        """Worker thread loop for processing tasks"""
        while self.running:
            try:
                # Get a task from the queue
                task = self.task_queue.get(timeout=1.0)
                
                # Track task as processing
                with self.processing_lock:
                    self.processing_tasks[task.id] = task
                
                try:
                    # Process the task with timeout if specified
                    if task.timeout:
                        # TODO: Implement timeout mechanism
                        result = self._process_task(task)
                    else:
                        result = self._process_task(task)
                    
                    # Call the callback with the result
                    if task.callback:
                        task.callback(result)
                    
                    # Update stats for successful completion
                    with self.stats_lock:
                        self.tasks_stats["completed"] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing task {task.id}: {str(e)}")
                    
                    # Try to retry the task if max retries not reached
                    if task.retries < task.max_retries:
                        task.retries += 1
                        
                        # If it was an OOM error, update stats
                        if isinstance(e, torch.cuda.OutOfMemoryError) or "CUDA out of memory" in str(e):
                            with self.stats_lock:
                                self.tasks_stats["oom_retries"] += 1
                        
                        # Re-queue the task with a delay
                        logger.info(f"Retrying task {task.id} (attempt {task.retries}/{task.max_retries})")
                        self.task_queue.put(task)
                    else:
                        # Max retries reached, call error callback
                        logger.error(f"Task {task.id} failed after {task.max_retries} attempts")
                        
                        # Update stats
                        with self.stats_lock:
                            self.tasks_stats["failed"] += 1
                        
                        # Call error callback if provided
                        if task.error_callback:
                            task.error_callback(e)
                finally:
                    # Remove task from processing tracking
                    with self.processing_lock:
                        self.processing_tasks.pop(task.id, None)
                    
                    # Mark task as done in queue
                    self.task_queue.task_done()
                    
            except queue.Empty:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error(f"Unexpected error in worker: {str(e)}")
    
    @oom_protected(retry_on_cpu=True)
    def _process_task(self, task: InferenceTask) -> Dict[str, Any]:
        """
        Process a single inference task
        
        Args:
            task: Task to process
            
        Returns:
            Inference results
        """
        # Check if we should try to batch this task with others
        if self.enable_batching and self.task_queue.qsize() > 0:
            # Try to create a batch of compatible tasks
            compatible_tasks = self._get_compatible_tasks(task)
            
            if compatible_tasks:
                logger.info(f"Batched {len(compatible_tasks)+1} compatible tasks")
                return self._process_batch([task] + compatible_tasks)
        
        # Process the task individually
        logger.debug(f"Processing task {task.id} on {task.device_preference}")
        
        # Move model to appropriate device if needed
        current_device = next(self.model.parameters()).device
        target_device = torch.device(task.device_preference)
        
        # Use memory-efficient context for inference
        with MemoryEfficientContext():
            if current_device != target_device:
                logger.debug(f"Moving model from {current_device} to {target_device}")
                self.model = self.model.to(target_device)
            
            # Move inputs to the appropriate device
            device_inputs = {}
            for k, v in task.inputs.items():
                if torch.is_tensor(v):
                    device_inputs[k] = v.to(target_device)
                else:
                    device_inputs[k] = v
            
            # Perform inference
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(**device_inputs)
                
            # Convert outputs to CPU before returning to save GPU memory
            if target_device.type == "cuda":
                outputs = {k: v.cpu() if torch.is_tensor(v) else v for k, v in outputs.items()}
            
            return outputs
    
    def _process_batch(self, tasks: List[InferenceTask]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Process a batch of compatible tasks
        
        Args:
            tasks: List of tasks to batch process
            
        Returns:
            Dictionary mapping task IDs to results
        """
        logger.debug(f"Processing batch of {len(tasks)} tasks")
        
        # Get the target device from the highest priority task
        target_device = torch.device(tasks[0].device_preference)
        
        # Process each input key separately for batching
        batch_inputs = {}
        unbatch_info = {}
        
        # Use memory-efficient context
        with MemoryEfficientContext():
            # Move model to the target device if needed
            current_device = next(self.model.parameters()).device
            if current_device != target_device:
                logger.debug(f"Moving model from {current_device} to {target_device}")
                self.model = self.model.to(target_device)
            
            # Prepare batched inputs
            for key in tasks[0].inputs.keys():
                # Check if this key exists in all tasks
                if all(key in task.inputs for task in tasks):
                    # Get all tensors for this input
                    tensors = [task.inputs[key] for task in tasks]
                    
                    # Check if all values are tensors
                    if all(torch.is_tensor(t) for t in tensors):
                        # Check shapes for compatibility
                        shapes = [t.shape for t in tensors]
                        if all(len(s) == len(shapes[0]) for s in shapes):
                            # Check if first dimension can be batched
                            if all(s[1:] == shapes[0][1:] for s in shapes):
                                # Batch the tensors
                                batch_inputs[key] = torch.cat([t.to(target_device) for t in tensors], dim=0)
                                # Store batch sizes for unbatching
                                unbatch_info[key] = [t.shape[0] for t in tensors]
                                continue
                    
                    # If we couldn't batch, just use the first one and log warning
                    logger.warning(f"Could not batch input key '{key}' due to incompatible shapes")
                    batch_inputs[key] = tensors[0].to(target_device)
                else:
                    # If not in all inputs, use the first one
                    batch_inputs[key] = tasks[0].inputs[key]
                    if torch.is_tensor(batch_inputs[key]):
                        batch_inputs[key] = batch_inputs[key].to(target_device)
            
            # Run batched inference
            self.model.eval()
            with torch.no_grad():
                batch_outputs = self.model(**batch_inputs)
            
            # Unbatch outputs
            results = {}
            offset = 0
            
            for i, task in enumerate(tasks):
                # Get this task's slice for each output
                task_results = {}
                
                for key, value in batch_outputs.items():
                    if torch.is_tensor(value) and key in unbatch_info:
                        # Get batch size for this task
                        batch_size = unbatch_info[key][i]
                        
                        # Extract this task's slice
                        task_results[key] = value[offset:offset+batch_size].cpu()
                    else:
                        # Non-tensor or non-batched output
                        task_results[key] = value
                
                # Store results
                results[task.id] = task_results
                
                # Update offset for next task
                if i < len(tasks) - 1:
                    offset += unbatch_info.get(list(batch_outputs.keys())[0], [1])[i]
            
            return results
    
    def _get_compatible_tasks(self, reference_task: InferenceTask) -> List[InferenceTask]:
        """
        Get compatible tasks that can be batched with the reference task
        
        Args:
            reference_task: Reference task to compare against
            
        Returns:
            List of compatible tasks
        """
        compatible_tasks = []
        
        # Only check a limited number of tasks
        max_checks = 50
        checks = 0
        
        # Check tasks in the queue
        tasks_to_check = []
        while not self.task_queue.empty() and checks < max_checks:
            try:
                tasks_to_check.append(self.task_queue.get_nowait())
                checks += 1
            except queue.Empty:
                break
        
        # Check for compatibility
        for task in tasks_to_check:
            # Check if device matches
            if task.device_preference != reference_task.device_preference:
                self.task_queue.put(task)  # Put back in queue
                continue
                
            # Check if input keys match
            if set(task.inputs.keys()) != set(reference_task.inputs.keys()):
                self.task_queue.put(task)  # Put back in queue
                continue
                
            # Check if input tensors can be batched (shape compatibility)
            can_batch = True
            for key in reference_task.inputs:
                ref_input = reference_task.inputs[key]
                task_input = task.inputs[key]
                
                if torch.is_tensor(ref_input) and torch.is_tensor(task_input):
                    # Check if shapes are compatible except for first dimension
                    if len(ref_input.shape) != len(task_input.shape):
                        can_batch = False
                        break
                    
                    if ref_input.shape[1:] != task_input.shape[1:]:
                        can_batch = False
                        break
            
            if can_batch:
                # Task can be batched
                compatible_tasks.append(task)
                
                # Stop if we've reached the maximum batch size
                if len(compatible_tasks) >= self.max_batch_size - 1:  # -1 because reference task is added later
                    break
            else:
                # Put back in queue
                self.task_queue.put(task)
        
        # Put back any remaining tasks
        for task in tasks_to_check:
            if task not in compatible_tasks:
                self.task_queue.put(task)
        
        return compatible_tasks
    
    def get_stats(self) -> Dict[str, int]:
        """Get current task statistics"""
        with self.stats_lock:
            stats = self.tasks_stats.copy()
        
        # Add current queue size and processing tasks
        stats["queued"] = self.task_queue.qsize()
        with self.processing_lock:
            stats["processing"] = len(self.processing_tasks)
        
        return stats
    
    def wait_for_tasks(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all tasks to complete
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if all tasks completed, False if timeout occurred
        """
        try:
            self.task_queue.join(timeout=timeout)
            return True
        except queue.Empty:
            return False

# Convenience function to create a scheduler
def create_inference_scheduler(model, max_workers=1, enable_batching=True) -> InferenceScheduler:
    """
    Create an inference scheduler for a model
    
    Args:
        model: Model to use for inference
        max_workers: Number of worker threads
        enable_batching: Whether to enable automatic batching
        
    Returns:
        InferenceScheduler instance
    """
    return InferenceScheduler(model, max_workers=max_workers, enable_batching=enable_batching)
