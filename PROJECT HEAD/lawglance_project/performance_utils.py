"""
Performance utilities for Lawglance system.

Provides tools for measuring and optimizing system performance.
"""
import time
import functools
import logging
import psutil
import os
from typing import List, Dict, Any, Callable, Optional

class PerformanceMonitor:
    """Monitors system performance for Lawglance."""
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.logger = logging.getLogger("lawglance.performance")
        self.function_stats = {}
    
    def timing_decorator(self, func):
        """Decorator to time function execution.
        
        Args:
            func: Function to time
            
        Returns:
            Decorated function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            result = func(*args, **kwargs)
            
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            execution_time = end_time - start_time
            memory_increase = end_memory - start_memory
            
            func_name = func.__name__
            if func_name not in self.function_stats:
                self.function_stats[func_name] = {
                    "calls": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "total_memory_increase": 0,
                    "avg_memory_increase": 0
                }
            
            stats = self.function_stats[func_name]
            stats["calls"] += 1
            stats["total_time"] += execution_time
            stats["avg_time"] = stats["total_time"] / stats["calls"]
            stats["total_memory_increase"] += memory_increase
            stats["avg_memory_increase"] = stats["total_memory_increase"] / stats["calls"]
            
            self.logger.debug(f"Function {func_name} executed in {execution_time:.4f}s with memory increase of {memory_increase:.2f}MB")
            
            return result
        
        return wrapper
    
    def _get_memory_usage(self):
        """Get current memory usage in MB.
        
        Returns:
            Memory usage in MB
        """
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)  # Convert to MB
    
    def get_function_stats(self):
        """Get statistics for monitored functions.
        
        Returns:
            Dictionary of function statistics
        """
        return self.function_stats
    
    def print_report(self):
        """Print performance report."""
        print("\nPerformance Report")
        print("=" * 80)
        print(f"{'Function':<30} {'Calls':<8} {'Avg Time (s)':<12} {'Total Time (s)':<12} {'Avg Memory (MB)':<16}")
        print("-" * 80)
        
        for name, stats in sorted(self.function_stats.items(), key=lambda x: x[1]["total_time"], reverse=True):
            print(f"{name:<30} {stats['calls']:<8} {stats['avg_time']:<12.4f} {stats['total_time']:<12.4f} {stats['avg_memory_increase']:<16.2f}")
        
        print("=" * 80)

class DocumentCacheOptimizer:
    """Optimizes document caching for Lawglance."""
    
    def __init__(self, cache, config):
        """Initialize the cache optimizer.
        
        Args:
            cache: Document cache to optimize
            config: Configuration object
        """
        self.cache = cache
        self.config = config
        self.logger = logging.getLogger("lawglance.cache_optimizer")
        self.access_counts = {}
        
    def track_access(self, file_path):
        """Track document access for optimization.
        
        Args:
            file_path: Path to accessed document
        """
        if file_path not in self.access_counts:
            self.access_counts[file_path] = 0
        self.access_counts[file_path] += 1
        
    def optimize_cache(self):
        """Optimize cache based on access patterns."""
        # Sort documents by access count
        sorted_docs = sorted(self.access_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Ensure most accessed documents are in cache
        for file_path, count in sorted_docs:
            if os.path.exists(file_path):
                self.logger.info(f"Ensuring document in cache: {file_path} (accessed {count} times)")
                
                # Preload content to ensure it's in cache
                content = self.cache.get_document_content(file_path)
                if content is None:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            self.cache.cache_document_content(file_path, content)
                    except Exception as e:
                        self.logger.error(f"Error loading document {file_path}: {e}")
        
        self.logger.info(f"Cache optimization complete for {len(sorted_docs)} documents")
        
    def get_access_stats(self):
        """Get document access statistics.
        
        Returns:
            Dictionary of access statistics
        """
        return {
            "access_counts": self.access_counts,
            "total_unique_documents": len(self.access_counts),
            "total_accesses": sum(self.access_counts.values())
        }

# Singleton instances for easy import
performance_monitor = PerformanceMonitor()
timing = performance_monitor.timing_decorator
