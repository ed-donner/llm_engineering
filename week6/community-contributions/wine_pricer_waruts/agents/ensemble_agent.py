from agents.agent import Agent
from agents.specialist_agent import SpecialistAgent
from agents.frontier_agent import FrontierAgent
from agents.neural_network_agent import NeuralNetworkAgent
from agents.preprocessor import Preprocessor


class EnsembleAgent(Agent):
    """
    An Agent that asks several pricing agents for an estimate and combines their answers
    """

    name = "Ensemble Agent"
    color = Agent.YELLOW

    # How much each model's opinion counts. These are Ed's weights; they must add up to 1
    FRONTIER_WEIGHT = 0.8
    SPECIALIST_WEIGHT = 0.1
    NEURAL_NETWORK_WEIGHT = 0.1

    def __init__(self, client, use_specialist: bool = True):
        """
        Create an instance of Ensemble, by creating each of the models
        :param client: an open QdrantClient, for the Frontier Agent's RAG search
        :param use_specialist: set to False to leave out the fine-tuned model on Modal
        """
        self.log("Initializing Ensemble Agent")
        self.specialist = SpecialistAgent() if use_specialist else None
        self.frontier = FrontierAgent(client)
        self.neural_network = NeuralNetworkAgent()
        self.preprocessor = Preprocessor()
        self.log("Ensemble Agent is ready")

    def price(self, description: str) -> float:
        """
        Run this ensemble model
        Rewrite the description into our summary format, ask each of the models to price the wine,
        then return the weighted average
        :param description: the description of a wine
        :return: an estimate of its price
        """
        self.log("Running Ensemble Agent - preprocessing text")
        rewrite = self.preprocessor.preprocess(description)
        self.log(f"Pre-processed text using {self.preprocessor.model_name}")
        frontier = self.frontier.price(rewrite)
        neural_network = self.neural_network.price(rewrite)
        if self.specialist:
            specialist = self.specialist.price(rewrite)
            combined = (
                frontier * self.FRONTIER_WEIGHT
                + specialist * self.SPECIALIST_WEIGHT
                + neural_network * self.NEURAL_NETWORK_WEIGHT
            )
        else:
            # Without the specialist, share its weight between the other two in proportion
            total = self.FRONTIER_WEIGHT + self.NEURAL_NETWORK_WEIGHT
            combined = (
                frontier * self.FRONTIER_WEIGHT + neural_network * self.NEURAL_NETWORK_WEIGHT
            ) / total
        self.log(f"Ensemble Agent complete - returning ${combined:.2f}")
        return combined
