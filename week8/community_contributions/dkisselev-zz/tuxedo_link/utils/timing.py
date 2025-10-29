"""Timing utilities for performance monitoring."""

import time
import functools
from typing import Callable, Any


def timed(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to time function execution and log it.
    
    Args:
        func: Function to be timed
        
    Returns:
        Wrapped function that logs execution time
        
    Usage:
        @timed
        def my_function():
            ...
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Wrapper function that times the execution."""
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        # Try to log if the object has a log method (Agent classes)
        if args and hasattr(args[0], 'log'):
            args[0].log(f"{func.__name__} completed in {elapsed:.2f} seconds")
        
        return result
    
    return wrapper

