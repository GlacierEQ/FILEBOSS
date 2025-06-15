"""
Utilities for DeepSeek-Coder
"""
from .memory_manager import get_memory_manager, setup_memory_protection
from .file_system_watcher import get_file_system_watcher
from .windows_integration import get_windows_integration
from .auto_offload import get_auto_offload, setup_auto_offload
from .model_loader import get_model_loader, load_model
from .memory_efficient_generation import create_generator
from .memory_efficient_batch_processor import MemoryEfficientBatchProcessor
from .model_memory_tracker import ModelMemoryTracker, get_model_memory_usage
from .tensor_optimization import TensorOptimizer, optimize_tensor
from .retry import retry
from .memory_diagnostics import MemoryDiagnostics
