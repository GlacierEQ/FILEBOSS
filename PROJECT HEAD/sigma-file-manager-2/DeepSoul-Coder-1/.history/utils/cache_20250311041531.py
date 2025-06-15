"""
Cache utilities for DeepSeek-Coder.
Provides caching mechanisms to improve performance and reduce redundant processing.
"""

import os
import time
import json
import hashlib
import logging
import threading
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from functools import wraps
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

class SqliteCache:
    """SQLite-based cache implementation with TTL support."""
    
    def __init__(self, db_path: str, ttl: int = 86400):
        """
        Initialize SQLite cache.
        
        Args:
            db_path: Path to the SQLite database file
            ttl: Default TTL in seconds (default: 1 day)
        """
        self.db_path = db_path
        self.ttl = ttl
        self.lock = threading.RLock()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        
        # Initialize the database
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create cache table with TTL support
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    created_at REAL,
                    expires_at REAL
                )
            ''')
            
            # Create index on expiration time for faster cleanup
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)
            ''')
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper locking."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            try:
                yield conn
            finally:
                conn.close()
    
    def _cleanup_expired(self, conn: sqlite3.Connection):
        """Remove expired entries from the cache."""
        now = time.time()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cache WHERE expires_at <= ?', (now,))
        deleted = cursor.rowcount
        if deleted > 0:
            logger.debug(f"Removed {deleted} expired items from cache")
        conn.commit()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            default: Default value if key is not found
        
        Returns:
            Cached value or default if not found
        """
        with self._get_connection() as conn:
            # Clean up expired entries
            self._cleanup_expired(conn)
            
            # Query the cache
            cursor = conn.cursor()
            cursor.execute(
                'SELECT value FROM cache WHERE key = ? AND expires_at > ?',
                (key, time.time())
            )
            
            row = cursor.fetchone()
            if row:
                try:
                    # Deserialize JSON
                    return json.loads(row[0])
                except Exception as e:
                    logger.warning(f"Error deserializing cache value for key {key}: {e}")
                    return default
            else:
                return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (uses instance default if None)
        
        Returns:
            True if value was successfully cached, False otherwise
        """
        # Use instance TTL if not specified
        ttl = ttl if ttl is not None else self.ttl
        
        try:
            # Serialize value to JSON
            value_json = json.dumps(value)
            
            # Calculate expiration time
            now = time.time()
            expires_at = now + ttl
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT OR REPLACE INTO cache (key, value, created_at, expires_at) VALUES (?, ?, ?, ?)',
                    (key, value_json, now, expires_at)
                )
                conn.commit()
                
                return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.
        
        Args:
            key: Cache key to delete
        
        Returns:
            True if key was deleted, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if cache was cleared, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM cache')
            conn.commit()
            
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total count
            cursor.execute('SELECT COUNT(*) FROM cache')
            total_count = cursor.fetchone()[0]
            
            # Get expired count
            now = time.time()
            cursor.execute('SELECT COUNT(*) FROM cache WHERE expires_at <= ?', (now,))
            expired_count = cursor.fetchone()[0]
            
            # Get size estimation
            cursor.execute('SELECT SUM(length(value)) FROM cache')
            total_size = cursor.fetchone()[0] or 0
            
            return {
                "total_entries": total_count,
                "expired_entries": expired_count,
                "active_entries": total_count - expired_count,
                "estimated_size_bytes": total_size,
                "db_path": self.db_path
            }


def cached(ttl: int = 3600, key_fn: Optional[Callable] = None):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time-to-live in seconds
        key_fn: Optional function to generate cache key from function arguments
    
    Returns:
        Decorated function with caching
    """
    def decorator(func):
        # Create a unique cache for this function
        cache_dir = os.path.join(
            os.environ.get("CACHE_DIR", "cache"),
            "function_cache"
        )
        os.makedirs(cache_dir, exist_ok=True)
        
        # Use function name and module in cache file name
        module_name = func.__module__.replace(".", "_")
        func_name = func.__name__
        db_path = os.path.join(cache_dir, f"{module_name}_{func_name}.db")
        
        # Create cache instance for this function
        cache = SqliteCache(db_path, ttl)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_fn is not None:
                cache_key = key_fn(*args, **kwargs)
            else:
                # Default: Hash the function name and arguments
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache first
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__} with key {cache_key}")
                return cached_value
            
            # Cache miss, call the function
            logger.debug(f"Cache miss for {func.__name__} with key {cache_key}")
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, ttl)
            
            return result
            
        # Add reference to cache object for management
        wrapper.cache = cache
        wrapper.clear_cache = cache.clear
        
        return wrapper
        
    return decorator


class MemoryCache:
    """In-memory cache implementation with TTL support."""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        """
        Initialize memory cache.
        
        Args:
            max_size: Maximum number of entries (LRU eviction when full)
            ttl: Default TTL in seconds (default: 5 minutes)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Tuple[Any, float]] = {}  # (value, expiry)
        self.lock = threading.RLock()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            default: Default value if key is not found or expired
        
        Returns:
            Cached value or default if not found
        """
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                
                # Check if expired
                if expiry > time.time():
                    return value
                else:
                    # Remove expired entry
                    del self.cache[key]
            
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses instance default if None)
        
        Returns:
            True if value was successfully cached
        """
        with self.lock:
            # Clean cache if it's getting too large
            if len(self.cache) >= self.max_size:
                self._cleanup_lru()
            
            # Set expiry time
            ttl = ttl if ttl is not None else self.ttl
            expiry = time.time() + ttl
            
            # Store value with expiry
            self.cache[key] = (value, expiry)
            
            return True
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.
        
        Args:
            key: Cache key to delete
        
        Returns:
            True if key was deleted, False if key not found
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if cache was cleared
        """
        with self.lock:
            self.cache.clear()
            return True
    
    def _cleanup_lru(self):
        """Remove least recently used entries when cache is full."""
        if not self.cache:
            return
        
        now = time.time()
        
        # First remove expired entries
        expired = [k for k, (_, exp) in self.cache.items() if exp <= now]
        for key in expired:
            del self.cache[key]
        
        # If still too many entries, remove LRU (approximation by using keys())
        if len(self.cache) >= self.max_size:
            # Remove 10% of entries (approximation of LRU)
            to_remove = max(1, self.max_size // 10)
            for key in list(self.cache.keys())[:to_remove]:
                del self.cache[key]


# Global cache instance for convenience
_default_cache = None

def get_cache() -> SqliteCache:
    """
    Get the default cache instance.
    
    Returns:
        Default cache instance
    """
    global _default_cache
    if _default_cache is None:
        cache_dir = os.environ.get("CACHE_DIR", "cache")
        os.makedirs(cache_dir, exist_ok=True)
        db_path = os.path.join(cache_dir, "deepseek_cache.db")
        _default_cache = SqliteCache(db_path)
    return _default_cache
