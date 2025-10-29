"""Base Agent class for Tuxedo Link agents."""

import logging
import time
from functools import wraps
from typing import Any, Callable


class Agent:
    """
    An abstract superclass for Agents.
    Used to log messages in a way that can identify each Agent.
    """

    # Foreground colors
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Background color
    BG_BLACK = '\033[40m'
    
    # Reset code to return to default color
    RESET = '\033[0m'

    name: str = ""
    color: str = '\033[37m'

    def log(self, message: str) -> None:
        """
        Log this as an info message, identifying the agent.
        
        Args:
            message: Message to log
        """
        color_code = self.BG_BLACK + self.color
        message = f"[{self.name}] {message}"
        logging.info(color_code + message + self.RESET)
    
    def log_error(self, message: str) -> None:
        """
        Log an error message.
        
        Args:
            message: Error message to log
        """
        color_code = self.BG_BLACK + self.RED
        message = f"[{self.name}] ERROR: {message}"
        logging.error(color_code + message + self.RESET)
    
    def log_warning(self, message: str) -> None:
        """
        Log a warning message.
        
        Args:
            message: Warning message to log
        """
        color_code = self.BG_BLACK + self.YELLOW
        message = f"[{self.name}] WARNING: {message}"
        logging.warning(color_code + message + self.RESET)


def timed(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to log execution time of agent methods.
    
    Args:
        func: Function to time
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        """Wrapper function that times and logs method execution."""
        start_time = time.time()
        result = func(self, *args, **kwargs)
        elapsed = time.time() - start_time
        self.log(f"{func.__name__} completed in {elapsed:.2f} seconds")
        return result
    return wrapper

