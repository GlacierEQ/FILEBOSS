"""
Authentication utilities for the DeepSeek-Coder API.
"""

import os
import time
import logging
import hashlib
import hmac
import secrets
from typing import List, Optional, Set

# Configure logging
logger = logging.getLogger(__name__)

class ApiKeyManager:
    """
    Manages API key validation and access control.
    """
    
    def __init__(self, env_var_name: str = "API_KEYS"):
        """
        Initialize the API key manager.
        
        Args:
            env_var_name: Environment variable name that contains API keys
        """
        self.env_var_name = env_var_name
        self._api_keys: Set[str] = set()
        self._load_api_keys()
    
    def _load_api_keys(self) -> None:
        """Load API keys from environment variable."""
        api_keys_str = os.environ.get(self.env_var_name, "")
        
        if not api_keys_str:
            logger.warning(f"No API keys found in environment variable {self.env_var_name}")
            return
        
        # Split by comma and strip whitespace
        api_keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]
        self._api_keys = set(api_keys)
        
        # Log number of keys loaded (not the keys themselves for security)
        logger.info(f"Loaded {len(self._api_keys)} API keys")
    
    def reload_api_keys(self) -> int:
        """
        Reload API keys from environment variable.
        
        Returns:
            Number of API keys loaded
        """
        self._api_keys.clear()
        self._load_api_keys()
        return len(self._api_keys)
    
    def is_valid_key(self, api_key: str) -> bool:
        """
        Check if an API key is valid.
        
        Args:
            api_key: API key to validate
        
        Returns:
            True if the API key is valid, False otherwise
        """
        # Simple validation - check if key exists in the set
        return api_key in self._api_keys
    
    def add_api_key(self, api_key: str) -> None:
        """
        Add a new API key (for testing purposes).
        
        Args:
            api_key: API key to add
        """
        self._api_keys.add(api_key)
        logger.info(f"Added new API key (total: {len(self._api_keys)})")
    
    def generate_api_key(self, prefix: str = "sk-") -> str:
        """
        Generate a new API key.
        
        Args:
            prefix: Prefix for the API key
        
        Returns:
            Newly generated API key
        """
        # Generate a random token
        random_bytes = secrets.token_bytes(32)
        key = prefix + secrets.token_hex(16)
        
        # Add to valid keys
        self.add_api_key(key)
        
        return key


# Default API key manager instance
_default_manager = None

def get_api_key_manager() -> ApiKeyManager:
    """
    Get or create the default API key manager.
    
    Returns:
        The default API key manager
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = ApiKeyManager()
    return _default_manager

def verify_api_key(api_key: str) -> bool:
    """
    Verify an API key.
    
    Args:
        api_key: API key to verify
    
    Returns:
        True if the API key is valid, False otherwise
    """
    manager = get_api_key_manager()
    return manager.is_valid_key(api_key)

def reload_api_keys() -> int:
    """
    Reload API keys from environment variable.
    
    Returns:
        Number of API keys loaded
    """
    manager = get_api_key_manager()
    return manager.reload_api_keys()

def generate_hmac_signature(api_key: str, message: str, timestamp: Optional[int] = None) -> str:
    """
    Generate an HMAC signature for request signing.
    
    Args:
        api_key: API key to use as the secret
        message: Message to sign
        timestamp: Optional timestamp to include in the signature
        
    Returns:
        HMAC signature as a hexadecimal string
    """
    if timestamp is None:
        timestamp = int(time.time())
    
    # Combine timestamp and message
    message_with_timestamp = f"{timestamp}:{message}"
    
    # Create HMAC signature
    signature = hmac.new(
        api_key.encode(),
        message_with_timestamp.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return signature
