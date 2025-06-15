"""
Rate limiting utilities for the DeepSeek-Coder API.
"""

import time
import logging
import threading
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, deque

# Configure logging
logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiter implementation supporting different limits per API key.
    Uses a sliding window algorithm to track requests within a time window.
    """
    
    def __init__(self, limit: int = 100, window: int = 3600, global_limit: int = 1000):
        """
        Initialize rate limiter.
        
        Args:
            limit: Default requests per window for each API key
            window: Time window in seconds
            global_limit: Global rate limit across all users
        """
        self.default_limit = limit
        self.window = window
        self.global_limit = global_limit
        
        # Store requests as (timestamp, count) tuples
        self.requests: Dict[str, List[Tuple[float, int]]] = defaultdict(list)
        self.custom_limits: Dict[str, int] = {}
        
        # Track global request count
        self.global_requests: List[Tuple[float, int]] = []
        
        # Add thread lock for thread safety
        self.lock = threading.RLock()
    
    def set_limit(self, key: str, limit: int):
        """
        Set custom rate limit for a specific API key.
        
        Args:
            key: API key or identifier
            limit: Custom rate limit
        """
        with self.lock:
            self.custom_limits[key] = limit
            logger.debug(f"Set custom rate limit for key '{key[:6]}...': {limit} requests per {self.window}s")
    
    def get_limit(self, key: str) -> int:
        """
        Get rate limit for a specific API key.
        
        Args:
            key: API key or identifier
        
        Returns:
            Rate limit for the specified key
        """
        with self.lock:
            return self.custom_limits.get(key, self.default_limit)
    
    def _prune_old_requests(self, requests_list: List[Tuple[float, int]]) -> List[Tuple[float, int]]:
        """
        Remove expired requests from the list.
        
        Args:
            requests_list: List of request timestamps and counts
            
        Returns:
            Updated list with expired requests removed
        """
        current_time = time.time()
        cutoff_time = current_time - self.window
        
        # Keep only requests within the window
        return [r for r in requests_list if r[0] >= cutoff_time]
    
    def _count_requests(self, requests_list: List[Tuple[float, int]]) -> int:
        """
        Count total requests in the list.
        
        Args:
            requests_list: List of request timestamps and counts
            
        Returns:
            Total count of requests
        """
        return sum(count for _, count in requests_list)
    
    def allow_request(self, key: str = "default", count: int = 1) -> bool:
        """
        Check if a request is allowed based on rate limits.
        Records the request if it's allowed.
        
        Args:
            key: API key or identifier
            count: Number of requests to record
            
        Returns:
            True if the request is allowed, False otherwise
        """
        with self.lock:
            current_time = time.time()
            
            # Clean up expired requests
            self.requests[key] = self._prune_old_requests(self.requests[key])
            self.global_requests = self._prune_old_requests(self.global_requests)
            
            # Calculate current usage
            key_usage = self._count_requests(self.requests[key])
            global_usage = self._count_requests(self.global_requests)
            
            # Get limit for this key
            key_limit = self.get_limit(key)
            
            # Check if adding this request would exceed limits
            if key_usage + count > key_limit:
                logger.warning(f"Rate limit exceeded for key '{key[:6]}...': {key_usage}/{key_limit}")
                return False
            
            if global_usage + count > self.global_limit:
                logger.warning(f"Global rate limit exceeded: {global_usage}/{self.global_limit}")
                return False
            
            # Record the request
            self.requests[key].append((current_time, count))
            self.global_requests.append((current_time, count))
            return True
    
    def get_usage(self, key: str = "default") -> Tuple[int, int]:
        """
        Get current usage and limit for a key.
        
        Args:
            key: API key or identifier
        
        Returns:
            Tuple of (current usage, limit)
        """
        with self.lock:
            # Clean up expired requests
            self.requests[key] = self._prune_old_requests(self.requests[key])
            
            # Calculate current usage
            usage = self._count_requests(self.requests[key])
            limit = self.get_limit(key)
            
            return usage, limit
    
    def get_remaining(self, key: str = "default") -> int:
        """
        Get remaining requests allowed for a key.
        
        Args:
            key: API key or identifier
            
        Returns:
            Number of remaining requests
        """
        usage, limit = self.get_usage(key)
        return max(0, limit - usage)
    
    def reset(self, key: Optional[str] = None):
        """
        Reset rate limit counters.
        
        Args:
            key: Optional key to reset (resets all if None)
        """
        with self.lock:
            if key is None:
                self.requests.clear()
                self.global_requests = []
                logger.info("Reset all rate limits")
            else:
                self.requests[key] = []
                logger.info(f"Reset rate limit for key '{key[:6]}...'")


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for more precise rate control.
    Useful for controlling token generation rates.
    """
    
    def __init__(self, rate: float = 10.0, capacity: int = 100):
        """
        Initialize token bucket rate limiter.
        
        Args:
            rate: Token refill rate per second
            capacity: Maximum capacity of the bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.RLock()
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Calculate new tokens to add
        new_tokens = elapsed * self.rate
        
        # Update tokens and cap at capacity
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
    
    def take(self, tokens: int = 1) -> bool:
        """
        Take tokens from the bucket.
        
        Args:
            tokens: Number of tokens to take
            
        Returns:
            True if tokens were successfully taken, False otherwise
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def get_available_tokens(self) -> float:
        """
        Get number of available tokens.
        
        Returns:
            Number of available tokens
        """
        with self.lock:
            self._refill()
            return self.tokens
