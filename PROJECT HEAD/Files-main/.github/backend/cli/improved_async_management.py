"""
Improved async/sync boundary management for CodexFlō CLI
"""
import asyncio
import logging
import functools
import time
from typing import Any, Callable, Coroutine, TypeVar, cast, Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')

def run_async(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., T]:
    """
    Decorator to run an async function in a new event loop.
    Handles the async/sync boundary properly.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop in this thread, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            # Don't close the loop if it was already running
            if not loop.is_running():
                loop.close()
    
    return wrapper

@asynccontextmanager
async def timeout_context(seconds: float):
    """
    Async context manager that raises TimeoutError if the body takes longer than specified seconds.
    """
    try:
        task = asyncio.current_task()
        if task is None:
            yield
            return
        
        # Set a timeout
        deadline = asyncio.create_task(asyncio.sleep(seconds))
        
        # Wait for either the deadline or the task to complete
        done, pending = await asyncio.wait(
            {deadline, task},
            return_when=asyncio.FIRST_COMPLETED
        )
        
        if deadline in done:
            # Timeout occurred
            raise TimeoutError(f"Operation timed out after {seconds} seconds")
        
        # Operation completed in time
        deadline.cancel()
        yield
    finally:
        # Cleanup
        try:
            deadline.cancel()
        except UnboundLocalError:
            pass

async def retry_async(
    func: Callable[..., Coroutine[Any, Any, T]],
    attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> T:
    """
    Retry an async function with exponential backoff.
    """
    last_exception = None
    for attempt in range(1, attempts + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < attempts:
                wait_time = delay * (backoff ** (attempt - 1))
                logger.warning(f"Attempt {attempt} failed, retrying in {wait_time:.1f}s: {e}")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {attempts} attempts failed")
                raise last_exception
    
    # This should never happen, but keeps type checkers happy
    assert last_exception is not None
    raise last_exception

# Example usage:
# @run_async
# async def main():
#     try:
#         async with timeout_context(5.0):
#             result = await retry_async(
#                 lambda: some_async_function(),
#                 attempts=3
#             )
#             return result
#     except TimeoutError:
#         logger.error("Operation timed out")
#         return None
# 
# result = main()