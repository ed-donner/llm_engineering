import modal
from agents.base_agent import Agent


class FTPriceAgent(Agent):
    """
    An Agent that runs the fine-tuned LLM that's running remotely on Modal
    """

    name = "FTPrice Agent"
    color = Agent.RED

    def __init__(self):
        """
        Set up this Agent by creating an instance of the modal class
        """
        self.log("FTPrice Agent is initializing - connecting to modal")
        Pricer = modal.Cls.from_name("llm-ft-pricer", "Pricer") #  1st API call: to fetch Pricer (remote class)
        self.pricer = Pricer()
        self.log("FTPrice Agent is ready")
        
    def price(self, description: str) -> float:
        """
        Make a remote call to return the estimate of the price of this item
        """
        self.log("FTPrice Agent is calling remote fine-tuned model")
        result = self.pricer.price.remote(description) # 2nd API call: to run the price method in the remote Pricer class
        self.log(f"FTPrice Agent completed - predicting ${result:.2f}")
        return result