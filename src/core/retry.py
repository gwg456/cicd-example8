"""
Retry logic with exponential backoff and jitter
"""
import asyncio
import functools
import logging
import random
import time
from typing import Any, Callable, Optional, Tuple, Type, Union

from tenacity import (
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
    wait_random,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
    RetryError
)

from .exceptions import RetryableError, TimeoutError, ConnectionError

logger = logging.getLogger(__name__)


# Default retryable exceptions
DEFAULT_RETRYABLE_EXCEPTIONS = (
    RetryableError,
    TimeoutError,
    ConnectionError,
    ConnectionResetError,
    BrokenPipeError,
    OSError,
)


def should_retry_exception(exc: Exception) -> bool:
    """
    Determine if an exception should trigger a retry
    
    Args:
        exc: The exception to check
    
    Returns:
        True if the exception should be retried
    """
    # Check if it's an AppException with retryable flag
    if hasattr(exc, 'retryable'):
        return exc.retryable
    
    # Check if it's in the default retryable exceptions
    return isinstance(exc, DEFAULT_RETRYABLE_EXCEPTIONS)


def retry_with_backoff(
    max_attempts: int = 3,
    max_delay: int = 60,
    min_delay: float = 1.0,
    max_jitter: float = 1.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        max_delay: Maximum delay between retries in seconds
        min_delay: Minimum delay between retries in seconds
        max_jitter: Maximum jitter to add to delay
        retryable_exceptions: Tuple of exceptions to retry on
        on_retry: Callback function called on each retry
    
    Example:
        @retry_with_backoff(max_attempts=5, max_delay=30)
        def fetch_data():
            # Function that might fail
            pass
    """
    exceptions = retryable_exceptions or DEFAULT_RETRYABLE_EXCEPTIONS
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    last_exception = e
                    
                    if attempt >= max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(min_delay * (2 ** (attempt - 1)), max_delay)
                    
                    # Add jitter
                    if max_jitter > 0:
                        delay += random.uniform(0, max_jitter)
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt)
                    
                    time.sleep(delay)
                except Exception as e:
                    # Non-retryable exception
                    logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                    raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def async_retry_with_backoff(
    max_attempts: int = 3,
    max_delay: int = 60,
    min_delay: float = 1.0,
    max_jitter: float = 1.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    Decorator for retrying async functions with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        max_delay: Maximum delay between retries in seconds
        min_delay: Minimum delay between retries in seconds
        max_jitter: Maximum jitter to add to delay
        retryable_exceptions: Tuple of exceptions to retry on
        on_retry: Callback function called on each retry
    
    Example:
        @async_retry_with_backoff(max_attempts=5, max_delay=30)
        async def fetch_data():
            # Async function that might fail
            pass
    """
    exceptions = retryable_exceptions or DEFAULT_RETRYABLE_EXCEPTIONS
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            last_exception = None
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    last_exception = e
                    
                    if attempt >= max_attempts:
                        logger.error(
                            f"Async function {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(min_delay * (2 ** (attempt - 1)), max_delay)
                    
                    # Add jitter
                    if max_jitter > 0:
                        delay += random.uniform(0, max_jitter)
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt)
                    
                    await asyncio.sleep(delay)
                except Exception as e:
                    # Non-retryable exception
                    logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                    raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def create_tenacity_retry(
    max_attempts: int = 3,
    max_seconds: int = 300,
    wait_min: float = 1.0,
    wait_max: float = 60.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
):
    """
    Create a tenacity retry decorator with custom configuration
    
    This uses the tenacity library for more advanced retry logic
    
    Args:
        max_attempts: Maximum number of attempts
        max_seconds: Maximum total time to retry in seconds
        wait_min: Minimum wait time between retries
        wait_max: Maximum wait time between retries
        retryable_exceptions: Exceptions to retry on
    
    Returns:
        Configured tenacity retry decorator
    """
    exceptions = retryable_exceptions or DEFAULT_RETRYABLE_EXCEPTIONS
    
    return retry(
        stop=(stop_after_attempt(max_attempts) | stop_after_delay(max_seconds)),
        wait=wait_exponential(multiplier=wait_min, max=wait_max) + wait_random(0, 1),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True,
    )


class RetryContext:
    """
    Context manager for retry operations
    
    Example:
        with RetryContext(max_attempts=3) as retry_ctx:
            while retry_ctx.should_retry():
                try:
                    # Operation that might fail
                    result = do_something()
                    retry_ctx.success()
                    return result
                except Exception as e:
                    retry_ctx.failure(e)
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        max_delay: int = 60,
        min_delay: float = 1.0,
        retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    ):
        self.max_attempts = max_attempts
        self.max_delay = max_delay
        self.min_delay = min_delay
        self.retryable_exceptions = retryable_exceptions or DEFAULT_RETRYABLE_EXCEPTIONS
        self.attempt = 0
        self.last_exception = None
        self._success = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val and not self._success:
            if self.should_retry() and isinstance(exc_val, self.retryable_exceptions):
                self.failure(exc_val)
                return True  # Suppress the exception
        return False
    
    def should_retry(self) -> bool:
        """Check if we should retry"""
        return self.attempt < self.max_attempts and not self._success
    
    def success(self):
        """Mark the operation as successful"""
        self._success = True
    
    def failure(self, exception: Exception):
        """Handle a failure"""
        self.attempt += 1
        self.last_exception = exception
        
        if self.attempt >= self.max_attempts:
            logger.error(f"Max retry attempts ({self.max_attempts}) reached")
            raise exception
        
        # Calculate delay
        delay = min(self.min_delay * (2 ** (self.attempt - 1)), self.max_delay)
        logger.warning(
            f"Attempt {self.attempt}/{self.max_attempts} failed: {exception}. "
            f"Retrying in {delay:.2f} seconds..."
        )
        time.sleep(delay)
    
    def get_delay(self) -> float:
        """Get the current retry delay"""
        return min(self.min_delay * (2 ** (self.attempt - 1)), self.max_delay)