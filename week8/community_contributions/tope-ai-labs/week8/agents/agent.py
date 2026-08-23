"""
Base Agent class for tope-ai-labs week8 multi-agent (based on week8 exercises).
"""
import logging


class Agent:
    """Abstract base for agents with colored logging."""

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BG_BLACK = "\033[40m"
    RESET = "\033[0m"

    name: str = "Agent"
    color: str = "\033[37m"

    def log(self, message: str) -> None:
        """Log message prefixed with agent name and color."""
        color_code = self.BG_BLACK + self.color
        msg = f"[{self.name}] {message}"
        logging.info(color_code + msg + self.RESET)
