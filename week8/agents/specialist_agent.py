# You're creating an AI agent => cloud-powered inference agent:
# Inherits from a base Agent class (agents.agent.Agent)
# Connects to a remote model service on Modal (pricer-service)
# Calls a method (price.remote(...)) to get predictions from the model running in the cloud
# Connects to a pre-trained model on Modal
# Makes predictions using .remote() to offload heavy computation
# Is structured cleanly for integration into larger agent workflows


import modal
from agents.agent import Agent

#Inherits from Agent, which could define standard logging, color, name, or action protocols for agents.

class SpecialistAgent(Agent):
    """
    An Agent that runs our fine-tuned LLM that's running remotely on Modal
    """

    name = "Specialist Agent"
    color = Agent.RED

    def __init__(self):
        """
        Set up this Agent by creating an instance of the modal class
        """
        self.log("Specialist Agent is initializing - connecting to modal")

        # remote class: Pricer;  registered Modal app: pricer-service
        Pricer = modal.Cls.from_name("pricer-service", "Pricer")
        self.pricer = Pricer()    # create a client instance to call methods in cloud
        self.log("Specialist Agent is ready")
        
    def price(self, description: str) -> float:
        """
        Make a remote call to return the estimate of the price of this item
        """
        self.log("Specialist Agent is calling remote fine-tuned model")

        # run price() method remotely on cloud-hosted Pricer class
        result = self.pricer.price.remote(description)
        
        self.log(f"Specialist Agent completed - predicting ${result:.2f}")
        return result
