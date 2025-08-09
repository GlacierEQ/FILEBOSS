""
Utility functions for the APEX MANUS integration hub.
"""
import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

def normalize_url(url: str) -> str:
    """
    Normalize a URL by removing query parameters and fragments.
    
    Args:
        url: The URL to normalize
        
    Returns:
        str: The normalized URL
    """
    if not url:
        return ""
    
    try:
        parsed = urlparse(url)
        normalized = parsed._replace(
            query="",
            fragment="",
            params=""
        )
        return urlunparse(normalized).rstrip("/")
    except Exception as e:
        logger.warning(f"Failed to normalize URL '{url}': {e}")
        return url

def generate_etag(data: Any) -> str:
    """
    Generate an ETag for the given data.
    
    Args:
        data: The data to generate an ETag for
        
    Returns:
        str: The generated ETag
    """
    import hashlib
    
    if isinstance(data, (dict, list)):
        data_str = json.dumps(data, sort_keys=True)
    elif isinstance(data, str):
        data_str = data
    else:
        data_str = str(data)
    
    return hashlib.md5(data_str.encode('utf-8')).hexdigest()

def parse_datetime(value: Union[str, datetime]) -> datetime:
    """
    Parse a datetime string or return the datetime object as-is.
    
    Args:
        value: The value to parse
        
    Returns:
        datetime: The parsed datetime
        
    Raises:
        ValueError: If the value cannot be parsed
    """
    if isinstance(value, datetime):
        return value
    
    # Try ISO 8601 format
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        pass
    
    # Try common formats
    for fmt in [
        '%Y-%m-%dT%H:%M:%S.%f%z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%Y%m%d%H%M%S',
        '%Y%m%d',
    ]:
        try:
            return datetime.strptime(value, fmt)
        except (ValueError, TypeError):
            continue
    
    raise ValueError(f"Could not parse datetime from '{value}'")

async def retry_async(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    **kwargs
) -> Any:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: The async function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
        **kwargs: Arguments to pass to the function
        
    Returns:
        The result of the function call
        
    Raises:
        Exception: If all attempts fail
    """
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            return await func(**kwargs)
        except exceptions as e:
            last_exception = e
            if attempt == max_attempts:
                break
                
            wait = delay * (backoff ** (attempt - 1))
            logger.warning(
                f"Attempt {attempt} failed: {e}. "
                f"Retrying in {wait:.1f} seconds..."
            )
            await asyncio.sleep(wait)
    
    raise last_exception or Exception("Unknown error in retry_async")

def sanitize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a dictionary by removing None values and converting non-serializable values.
    
    Args:
        d: The dictionary to sanitize
        
    Returns:
        Dict: The sanitized dictionary
    """
    def _sanitize_value(v: Any) -> Any:
        if v is None:
            return ""
        if isinstance(v, (str, int, float, bool)):
            return v
        if isinstance(v, (list, tuple, set)):
            return [_sanitize_value(x) for x in v]
        if isinstance(v, dict):
            return {str(k): _sanitize_value(v) for k, v in v.items()}
        if hasattr(v, 'isoformat'):
            return v.isoformat()
        return str(v)
    
    return {k: _sanitize_value(v) for k, v in d.items() if v is not None}
