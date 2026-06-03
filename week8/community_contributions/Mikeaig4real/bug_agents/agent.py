"""
Base Agent class for the Bug Hunter Framework.
Provides logging and color utilities, mirroring week8/agents/agent.py.
"""

import logging


class Agent:
    """Base class for all bug hunter agents."""

    # Terminal colors for logging
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

    name = "Agent"
    color = CYAN

    def log(self, message: str):
        """Log a colored message to the console."""
        text = f"{self.color}[{self.name}] {message}{self.RESET}"
        logging.info(text)
