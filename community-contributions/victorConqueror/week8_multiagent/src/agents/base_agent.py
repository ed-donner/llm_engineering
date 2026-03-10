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
    
    def price(self, description: str) -> float:
        """
        Estimate the price of a product
        Override this in subclasses
        """
        raise NotImplementedError("Subclasses must implement price()")
    
    def price_with_confidence(self, description: str) -> tuple[float, float]:
        """
        Estimate price with confidence score
        Returns (price, confidence) where confidence is 0-1
        Override this in subclasses for better confidence estimation
        """
        price = self.price(description)
        return price, 0.5  # Default confidence
