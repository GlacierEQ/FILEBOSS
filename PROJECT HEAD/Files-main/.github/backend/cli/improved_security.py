"""
Improved security and input sanitization for CodexFlō CLI
"""
import os
import re
import logging
import secrets
import base64
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

logger = logging.getLogger(__name__)

class SecurityError(Exception):
    """Security-related error"""
    pass

def sanitize_path(path: str, base_dir: Optional[str] = None) -> Path:
    """
    Sanitize and validate a file path to prevent path traversal attacks.
    
    Args:
        path: The path to sanitize
        base_dir: Optional base directory to restrict paths to
        
    Returns:
        Resolved Path object
        
    Raises:
        SecurityError: If path validation fails
    """
    try:
        # Convert to absolute path
        path_obj = Path(path).expanduser().resolve()
        
        # If base_dir is provided, ensure path is within it
        if base_dir:
            base_path = Path(base_dir).expanduser().resolve()
            if not str(path_obj).startswith(str(base_path)):
                raise SecurityError(f"Path {path} is outside allowed directory {base_dir}")
        
        return path_obj
    except Exception as e:
        if isinstance(e, SecurityError):
            raise
        raise SecurityError(f"Invalid path: {e}")

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal and command injection.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = os.path.basename(filename)
    
    # Replace potentially dangerous characters
    filename = re.sub(r'[^\w\.-]', '_', filename)
    
    # Ensure filename doesn't start with dangerous characters
    if filename.startswith(('.', '-')):
        filename = f"safe_{filename}"
    
    return filename

def secure_api_key_storage(api_key: str, key_name: str) -> str:
    """
    Securely store API key in environment variable or keyring.
    
    Args:
        api_key: The API key to store
        key_name: Name/identifier for the API key
        
    Returns:
        Reference to the stored key
    """
    # In a real implementation, this would use keyring or a similar secure storage
    # For this example, we'll just set an environment variable
    env_var_name = f"CODEXFLO_{key_name.upper()}_API_KEY"
    os.environ[env_var_name] = api_key
    
    # Return reference that can be stored in config
    return f"${{{env_var_name}}}"

def get_secure_api_key(key_reference: str) -> Optional[str]:
    """
    Retrieve API key from secure storage.
    
    Args:
        key_reference: Reference to the stored key (e.g., "${ENV_VAR_NAME}")
        
    Returns:
        The API key or None if not found
    """
    if key_reference.startswith("${") and key_reference.endswith("}"):
        env_var = key_reference[2:-1]
        return os.environ.get(env_var)
    return None

def validate_command_args(args: List[str]) -> bool:
    """
    Validate command arguments to prevent command injection.
    
    Args:
        args: List of command arguments
        
    Returns:
        True if arguments are safe, False otherwise
    """
    # Check for shell metacharacters or injection attempts
    dangerous_patterns = [
        r'[;&|`$]',  # Shell metacharacters
        r'\s*>\s*',  # Redirection
        r'\s*<\s*',  # Redirection
        r'\s*>>\s*', # Append redirection
        r'\s*\|\s*', # Pipe
    ]
    
    for arg in args:
        if not isinstance(arg, str):
            continue
            
        for pattern in dangerous_patterns:
            if re.search(pattern, arg):
                logger.warning(f"Potentially dangerous command argument detected: {arg}")
                return False
    
    return True

# Example usage:
# try:
#     safe_path = sanitize_path(user_input, base_dir="/safe/directory")
#     safe_filename = sanitize_filename(user_input_filename)
#     
#     # For API keys
#     key_ref = secure_api_key_storage("sk-actual-api-key", "openai")
#     # Later retrieve with:
#     api_key = get_secure_api_key(key_ref)
# except SecurityError as e:
#     logger.error(f"Security violation: {e}")