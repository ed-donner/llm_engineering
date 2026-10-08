import modal
from agents.agent import Agent


class SpecialistAgent(Agent):
    """
    An Agent that runs our fine-tuned LLM running remotely on Modal
    """

    name = "Specialist Agent"
    color = Agent.RED

    def __init__(self):
        """
        Set up this Agent by creating an instance of the modal class
        """
        self.log("Specialist Agent is initializing - connection to modal...")
        Pricer = modal.Cls.from_name("pricer-service", "Pricer")
        self.pricer = Pricer()
        self.log("Specialist Agent is ready")


    def price(self, description: str) -> float:
        """
            Make a remote calll to return the estimate of the price of the item
        """
        self.log("Specialist Agent is calling remote fine-tuned model")
        result = self.pricer.price.remote(description)
        self.log(f"Specialist Agent completed - predicting ${result:.2f}")
        return result
    
    
