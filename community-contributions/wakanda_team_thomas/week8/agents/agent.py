import logging

logger = logging.getLogger(__name__)

COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}
RESET = "\033[0m"


class Agent:
    """Base class for all rental deal agents."""

    name: str = "Agent"
    color: str = "white"

    def log(self, message: str):
        color_code = COLORS.get(self.color, COLORS["white"])
        formatted = f"{color_code}[{self.name}] {message}{RESET}"
        logger.info(formatted)
        print(formatted)
