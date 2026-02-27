"""
Retry utilities for handling failures with exponential backoff.
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Optional
import random

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to delay
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        # Calculate delay with exponential backoff
                        if jitter:
                            delay = min(
                                initial_delay * (exponential_base ** attempt) + random.uniform(0, 1),
                                max_delay
                            )
                        else:
                            delay = min(
                                initial_delay * (exponential_base ** attempt),
                                max_delay
                            )
                        
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            # Re-raise last exception if all attempts failed
            raise last_exception
        
        return wrapper
    return decorator


class RetryHandler:
    """Class for managing retry logic with state."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.attempt_count = 0
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        delay = self.initial_delay
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                result = func(*args, **kwargs)
                self.attempt_count = 0  # Reset on success
                return result
            except Exception as e:
                last_exception = e
                self.attempt_count = attempt + 1
                
                if attempt < self.max_attempts - 1:
                    delay = min(
                        self.initial_delay * (self.exponential_base ** attempt),
                        self.max_delay
                    )
                    logger.warning(
                        f"Retry attempt {attempt + 1}/{self.max_attempts}: {e}. "
                        f"Waiting {delay:.2f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Max retries reached: {e}")
        
        raise last_exception
    
    def reset(self):
        """Reset attempt counter."""
        self.attempt_count = 0
