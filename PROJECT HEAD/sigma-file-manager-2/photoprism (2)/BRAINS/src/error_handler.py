"""
Standardized error handling for Sorting Hat

This module provides a unified approach to error handling,
logging, and user feedback across the application.
"""
import os
import sys
import logging
import traceback
from typing import Any, Dict, Optional, Callable, Type, Union

# Import the config module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import config, get_log_level

# Configure logging
logging.basicConfig(
    level=getattr(logging, get_log_level()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(config.get("paths.logs_dir"), "sorting_hat.log")),
        logging.StreamHandler()
    ]
)

class SortingHatError(Exception):
    """Base exception class for Sorting Hat errors"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        """
        Initialize a SortingHatError
        
        Args:
            message: Human-readable error message
            error_code: Optional error code for categorization
            details: Optional dictionary with additional error details
        """
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict:
        """Convert the error to a dictionary representation"""
        return {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }

class PathError(SortingHatError):
    """Error related to file paths"""
    def __init__(self, message: str, path: str, details: Dict = None):
        super().__init__(
            message=message,
            error_code="PATH_ERROR",
            details={"path": path, **(details or {})}
        )

class APIError(SortingHatError):
    """Error related to API calls"""
    def __init__(self, message: str, api_name: str, details: Dict = None):
        super().__init__(
            message=message,
            error_code="API_ERROR",
            details={"api_name": api_name, **(details or {})}
        )

class ConfigError(SortingHatError):
    """Error related to configuration"""
    def __init__(self, message: str, config_key: str = None, details: Dict = None):
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            details={"config_key": config_key, **(details or {})}
        )

class FileOperationError(SortingHatError):
    """Error related to file operations"""
    def __init__(self, message: str, operation: str, path: str, details: Dict = None):
        super().__init__(
            message=message,
            error_code="FILE_OPERATION_ERROR",
            details={"operation": operation, "path": path, **(details or {})}
        )

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def handle_exception(
    func: Callable = None,
    error_types: Union[Type[Exception], tuple] = Exception,
    default_return: Any = None,
    log_level: str = "ERROR",
    reraise: bool = False
) -> Callable:
    """
    Decorator for handling exceptions in a standardized way
    
    Args:
        func: Function to decorate
        error_types: Exception type(s) to catch
        default_return: Value to return on error
        log_level: Logging level for errors
        reraise: Whether to reraise the exception after handling
        
    Returns:
        Decorated function
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except error_types as e:
                logger = get_logger(f.__module__)
                log_method = getattr(logger, log_level.lower())
                
                # Get traceback information
                tb = traceback.format_exc()
                
                # Log the error
                log_method(f"Error in {f.__name__}: {str(e)}\n{tb}")
                
                # Reraise if requested
                if reraise:
                    raise
                
                # Return default value
                return default_return
        return wrapper
    
    # Allow use as @handle_exception or @handle_exception()
    if func is None:
        return decorator
    return decorator(func)

def safe_path_operation(
    func: Callable = None,
    operation_name: str = "file operation",
    default_return: Any = None
) -> Callable:
    """
    Decorator for safely handling file path operations
    
    Args:
        func: Function to decorate
        operation_name: Name of the operation for error messages
        default_return: Value to return on error
        
    Returns:
        Decorated function
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except (OSError, IOError) as e:
                # Extract path from error if possible
                path = getattr(e, "filename", "unknown path")
                
                # Log the error
                logger = get_logger(f.__module__)
                logger.error(f"Error during {operation_name} on {path}: {str(e)}")
                
                # Convert to our standard error type
                raise FileOperationError(
                    message=f"Failed to {operation_name}: {str(e)}",
                    operation=operation_name,
                    path=path
                ) from e
            except Exception as e:
                # Handle other exceptions
                logger = get_logger(f.__module__)
                logger.error(f"Unexpected error during {operation_name}: {str(e)}")
                
                # Reraise as our standard error type
                raise SortingHatError(
                    message=f"Unexpected error during {operation_name}: {str(e)}",
                    error_code="UNEXPECTED_ERROR"
                ) from e
        return wrapper
    
    # Allow use as @safe_path_operation or @safe_path_operation()
    if func is None:
        return decorator
    return decorator(func)

def format_error_for_user(error: Exception) -> str:
    """
    Format an error message for user display
    
    Args:
        error: The exception to format
        
    Returns:
        User-friendly error message
    """
    if isinstance(error, SortingHatError):
        return error.message
    
    # Map common errors to user-friendly messages
    if isinstance(error, FileNotFoundError):
        return f"File not found: {error.filename}"
    elif isinstance(error, PermissionError):
        return f"Permission denied: {getattr(error, 'filename', 'unknown file')}"
    elif isinstance(error, OSError):
        return f"System error: {str(error)}"
    
    # Generic error message
    return f"An error occurred: {str(error)}"
