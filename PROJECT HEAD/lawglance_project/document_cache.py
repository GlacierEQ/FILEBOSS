"""
Document caching system for Lawglance.
Provides caching for document content and processed results.
"""
import os
import json
import hashlib
import time
from typing import Dict, Any, Optional, List, Tuple
from collections import OrderedDict

class LRUCache:
    """Least Recently Used (LRU) cache for documents."""
    
    def __init__(self, capacity: int = 100):
        """Initialize the LRU cache.
        
        Args:
            capacity: Maximum number of items to store
        """
        self.cache = OrderedDict()
        self.capacity = capacity
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if key not in self.cache:
            return None
        
        # Move to end to show it was recently used
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: str, value: Any) -> None:
        """Put item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # Remove least recently used item if at capacity
        if len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        
        self.cache[key] = value
        self.cache.move_to_end(key)
    
    def keys(self) -> List[str]:
        """Get all keys in cache.
        
        Returns:
            List of cache keys
        """
        return list(self.cache.keys())
    
    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()

class DocumentCache:
    """Document caching system for Lawglance."""
    
    def __init__(self, config):
        """Initialize the document cache.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.enabled = config.get("caching", "enabled")
        self.max_size = config.get("caching", "max_cache_size")
        self.cache_dir = config.get("caching", "cache_dir")
        
        # Create cache directory if it doesn't exist
        if self.enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
        
        # In-memory caches
        self.content_cache = LRUCache(self.max_size)
        self.analysis_cache = LRUCache(self.max_size)
        self.embedding_cache = LRUCache(self.max_size)
    
    def get_document_content(self, file_path: str) -> Optional[str]:
        """Get document content from cache.
        
        Args:
            file_path: Path to document
            
        Returns:
            Document content or None if not cached
        """
        if not self.enabled:
            return None
        
        cache_key = self._get_cache_key(file_path)
        cached = self.content_cache.get(cache_key)
        
        if cached is None:
            # Try to get from disk cache
            disk_cache = self._load_disk_cache(cache_key)
            if disk_cache and "content" in disk_cache:
                self.content_cache.put(cache_key, disk_cache["content"])
                return disk_cache["content"]
        
        return cached
    
    def cache_document_content(self, file_path: str, content: str) -> None:
        """Cache document content.
        
        Args:
            file_path: Path to document
            content: Document content
        """
        if not self.enabled:
            return
        
        cache_key = self._get_cache_key(file_path)
        self.content_cache.put(cache_key, content)
        
        # Update disk cache
        disk_cache = self._load_disk_cache(cache_key) or {}
        disk_cache["content"] = content
        disk_cache["timestamp"] = time.time()
        self._save_disk_cache(cache_key, disk_cache)
    
    def get_document_analysis(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get document analysis from cache.
        
        Args:
            file_path: Path to document
            
        Returns:
            Document analysis or None if not cached
        """
        if not self.enabled:
            return None
        
        cache_key = self._get_cache_key(file_path)
        cached = self.analysis_cache.get(cache_key)
        
        if cached is None:
            # Try to get from disk cache
            disk_cache = self._load_disk_cache(cache_key)
            if disk_cache and "analysis" in disk_cache:
                self.analysis_cache.put(cache_key, disk_cache["analysis"])
                return disk_cache["analysis"]
        
        return cached
    
    def cache_document_analysis(self, file_path: str, analysis: Dict[str, Any]) -> None:
        """Cache document analysis.
        
        Args:
            file_path: Path to document
            analysis: Document analysis
        """
        if not self.enabled:
            return
        
        cache_key = self._get_cache_key(file_path)
        self.analysis_cache.put(cache_key, analysis)
        
        # Update disk cache
        disk_cache = self._load_disk_cache(cache_key) or {}
        disk_cache["analysis"] = analysis
        disk_cache["timestamp"] = time.time()
        self._save_disk_cache(cache_key, disk_cache)
    
    def get_document_embeddings(self, file_path: str) -> Optional[Any]:
        """Get document embeddings from cache.
        
        Args:
            file_path: Path to document
            
        Returns:
            Document embeddings or None if not cached
        """
        if not self.enabled:
            return None
        
        cache_key = self._get_cache_key(file_path)
        return self.embedding_cache.get(cache_key)
    
    def cache_document_embeddings(self, file_path: str, embeddings: Any) -> None:
        """Cache document embeddings.
        
        Args:
            file_path: Path to document
            embeddings: Document embeddings
        """
        if not self.enabled:
            return
        
        cache_key = self._get_cache_key(file_path)
        self.embedding_cache.put(cache_key, embeddings)
    
    def invalidate(self, file_path: str) -> None:
        """Invalidate cache for a document.
        
        Args:
            file_path: Path to document
        """
        if not self.enabled:
            return
        
        cache_key = self._get_cache_key(file_path)
        
        # Remove from in-memory caches
        for cache in [self.content_cache, self.analysis_cache, self.embedding_cache]:
            if cache.get(cache_key) is not None:
                cache.put(cache_key, None)
        
        # Remove from disk cache
        disk_cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(disk_cache_path):
            os.remove(disk_cache_path)
    
    def clear(self) -> None:
        """Clear all caches."""
        if not self.enabled:
            return
        
        # Clear in-memory caches
        self.content_cache.clear()
        self.analysis_cache.clear()
        self.embedding_cache.clear()
        
        # Clear disk cache
        for file in os.listdir(self.cache_dir):
            if file.endswith(".json"):
                os.remove(os.path.join(self.cache_dir, file))
    
    def _get_cache_key(self, file_path: str) -> str:
        """Generate cache key for a document.
        
        Args:
            file_path: Path to document
            
        Returns:
            Cache key
        """
        # Use absolute path to avoid issues with relative paths
        abs_path = os.path.abspath(file_path)
        
        try:
            # Include file modification time in key to detect changes
            mtime = os.path.getmtime(abs_path)
            key_data = f"{abs_path}:{mtime}"
        except FileNotFoundError:
            key_data = abs_path
        
        # Use MD5 hash of path as key
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()
    
    def _load_disk_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Load disk cache for a document.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Disk cache data or None if not found
        """
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If cache file is corrupted, remove it
                os.remove(cache_path)
        
        return None
    
    def _save_disk_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Save disk cache for a document.
        
        Args:
            cache_key: Cache key
            data: Data to cache
        """
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f)
        except IOError:
            pass  # Ignore write errors
