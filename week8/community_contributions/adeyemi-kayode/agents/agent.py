"""
Base agent for the Africa flight price autonomous multi-agent system.
Reference: week8 agents/agent.py
"""

import logging

class Agent:
    """
    Abstract base for all agents. Provides colored logging by agent name.
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
    color: str = "\033[37m"

    def log(self, message: str) -> None:
        color_code = self.BG_BLACK + self.color
        logging.info(color_code + f"[{self.name}] {message}" + self.RESET)
