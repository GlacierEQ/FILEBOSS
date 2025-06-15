"""
Retry Utility - Decorator for retrying functions that may fail transiently
"""
import time
import logging
import functools
from typing import Callable, Type, Tuple

logger = logging.getLogger("DeepSoul-Retry")

def retry(exceptions: Tuple[Type[Exception]], tries: int = 3, delay: int = 2, backoff: int = 2):
    """
    Retry calling the decorated function using an exponential backoff.
    
    Args:
        exceptions: The exception or exceptions to check. May be a tuple of exceptions.
        tries: Number of times to try (not retry) before giving up.
        delay: Initial delay between retries in seconds.
        backoff: Backoff multiplier (e.g., value of 2 will double the delay each retry).
    """
    def retry_decorator(func):
        @functools.wraps(func)
        def retry_wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    msg = f"Retrying in {mdelay} seconds ({mtries-1} tries remaining) after {type(e).__name__}: {str(e)}"
                    logger.warning(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)  # Last attempt
        return retry_wrapper
    return retry_decorator
