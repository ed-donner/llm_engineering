import logging


class Agent:
    """
    Base class for all price estimation agents.
    Provides logging functionality with colored output.
    """

    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BG_BLACK = '\033[40m'
    RESET = '\033[0m'

    name: str = "Base Agent"
    color: str = WHITE

    def log(self, message: str):
        """Log a message with agent identification and color."""
        color_code = self.BG_BLACK + self.color
        formatted = f"[{self.name}] {message}"
        logging.info(color_code + formatted + self.RESET)
