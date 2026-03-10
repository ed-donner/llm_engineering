import logging


class Agent:
    """
    Abstract base class for all Study Resource Scout agents.
    """

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BG_BLACK = "\033[40m"
    RESET = "\033[0m"

    name: str = ""
    color: str = WHITE

    def log(self, message: str) -> None:
        color_code = self.BG_BLACK + self.color
        payload = f"[{self.name}] {message}"
        logging.info(color_code + payload + self.RESET)
