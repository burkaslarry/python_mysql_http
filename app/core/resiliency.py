"""
Resiliency Engine: Retry Logic with Exponential Backoff
Handles timeouts, retries, and standardized error responses.
"""

import asyncio
import logging
from typing import Callable, Any, TypeVar, Awaitable
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Backoff schedule: (retry_count, delay_in_seconds, timeout_limit_in_seconds)
BACKOFF_SCHEDULE = [
    (0, 0.0, 0.2),      # Initial attempt: 200ms timeout, no delay
    (1, 0.4, 0.4),      # Retry 1: 400ms delay, 400ms timeout
    (2, 0.8, 0.8),      # Retry 2: 800ms delay, 800ms timeout
    (3, 1.6, 1.6),      # Retry 3: 1600ms delay, 1600ms timeout
]


class ResiliencyException(Exception):
    """Base exception for resiliency-related errors."""
    def __init__(self, message: str, retry_count: int = 0, error_code: str = "500"):
        self.message = message
        self.retry_count = retry_count
        self.error_code = error_code
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        super().__init__(self.message)


class GatewayTimeoutException(ResiliencyException):
    """Raised when all retries are exhausted (504)."""
    def __init__(self, message: str, retry_count: int):
        super().__init__(message, retry_count, "504")


class ServiceUnavailableException(ResiliencyException):
    """Raised when database is unavailable (503)."""
    def __init__(self, message: str, retry_count: int = 0):
        super().__init__(message, retry_count, "503")


async def execute_with_retries(
    coro_func: Callable[..., Awaitable[T]],
    *args,
    **kwargs
) -> T:
    """
    Execute an async function with exponential backoff retry logic.
    
    Args:
        coro_func: Async function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
    
    Returns:
        Result of the function execution
    
    Raises:
        GatewayTimeoutException: If all retries fail due to timeout
        ServiceUnavailableException: If database is unavailable
    """
    last_exception = None
    
    for retry_count, delay, timeout_limit in BACKOFF_SCHEDULE:
        try:
            # Apply delay before retry (not on initial attempt)
            if delay > 0:
                logger.debug(f"Retry {retry_count}: Waiting {delay}s before attempt")
                await asyncio.sleep(delay)
            
            # Execute with timeout
            logger.debug(f"Attempt {retry_count}: Executing with {timeout_limit}s timeout")
            result = await asyncio.wait_for(
                coro_func(*args, **kwargs),
                timeout=timeout_limit
            )
            logger.debug(f"Attempt {retry_count}: Success")
            return result
        
        except asyncio.TimeoutError as e:
            last_exception = e
            logger.warning(
                f"Attempt {retry_count}: Timeout (limit: {timeout_limit}s). "
                f"Retries remaining: {len(BACKOFF_SCHEDULE) - retry_count - 1}"
            )
        
        except Exception as e:
            last_exception = e
            logger.warning(
                f"Attempt {retry_count}: Exception - {str(e)}. "
                f"Retries remaining: {len(BACKOFF_SCHEDULE) - retry_count - 1}"
            )
    
    # All retries exhausted
    retry_count = len(BACKOFF_SCHEDULE) - 1
    logger.error(f"All retries exhausted after {retry_count + 1} attempts")
    
    raise GatewayTimeoutException(
        f"Database operation timed out after {retry_count + 1} attempts. "
        f"Last error: {str(last_exception)}",
        retry_count=retry_count + 1
    )


async def execute_with_fallback(
    coro_func: Callable[..., Awaitable[T]],
    fallback_value: T,
    *args,
    **kwargs
) -> T:
    """
    Execute an async function with retry logic and fallback value.
    
    Args:
        coro_func: Async function to execute
        fallback_value: Value to return if all retries fail
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
    
    Returns:
        Result of the function execution or fallback_value
    """
    try:
        return await execute_with_retries(coro_func, *args, **kwargs)
    except ResiliencyException as e:
        logger.warning(f"Returning fallback value due to: {e.message}")
        return fallback_value
