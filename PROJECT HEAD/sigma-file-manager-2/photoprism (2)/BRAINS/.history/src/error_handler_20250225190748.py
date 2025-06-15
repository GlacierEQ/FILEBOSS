import logging
import traceback
from fastapi import HTTPException
from typing import Dict, Any, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("error_logs.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("llama-fs")

class AppError(Exception):
    """Base exception class for application errors with status code and detail message"""
    def __init__(self, status_code: int = 500, detail: str = "An unexpected error occurred"):
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.detail)

def handle_error(func: Callable) -> Callable:
    """Decorator for request handlers to catch and log exceptions"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException as e:
            # Re-raise FastAPI HTTP exceptions
            logger.warning(f"HTTP error: {e.status_code} - {e.detail}")
            raise
        except AppError as e:
            # Handle our custom application errors
            logger.error(f"Application error: {e.status_code} - {e.detail}")
            raise HTTPException(status_code=e.status_code, detail=e.detail)
        except Exception as e:
            # Handle unexpected exceptions
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            raise HTTPException(status_code=500, detail="An internal server error occurred")
    
    return wrapper

def safe_process(func: Callable, fallback_value: Any = None, log_error: bool = True) -> Callable:
    """Utility for safely executing functions that might fail"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_error:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                logger.debug(traceback.format_exc())
            return fallback_value
    
    return wrapper

def format_error_response(error: Exception, include_traceback: bool = False) -> Dict[str, Any]:
    """Format error details for API responses"""
    response = {
        "error": str(error),
        "error_type": error.__class__.__name__
    }
    
    if include_traceback:
        response["traceback"] = traceback.format_exc()
        
    return response
