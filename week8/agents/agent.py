#This Python code defines an abstract base class called Agent, which is meant to be used as a #superclass for other agent-like classes in a system (such as AI agents, bots, etc.). Its main #feature is to log messages with color-coded output, which is helpful in environments like a # #terminal or command line where you want to visually distinguish output from different agents.

# https://chatgpt.com/share/6841f3f8-e21c-8001-9e15-074290f17aa4


import logging

class Agent:
    """
    An abstract superclass for Agents
    Used to log messages in a way that can identify each Agent
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

    def log(self, message):
        """
        Log this as an info message, identifying the agent
        """
        color_code = self.BG_BLACK + self.color
        message = f"[{self.name}] {message}"
        logging.info(color_code + message + self.RESET)