from agents.agent import Agent
from agents.specialist_agent import SpecialistAgent
from agents.frontier_agent import FrontierAgent
from agents.preprocessor import Preprocessor


class EnsembleAgent(Agent):
    """
    Combines salary estimates from the specialist (fine-tuned) model and the
    frontier (RAG) model. Weights can be tuned via linear regression on
    validation data for better accuracy.
    """

    name = "Ensemble Agent"
    color = Agent.YELLOW

    FRONTIER_WEIGHT = 0.6
    SPECIALIST_WEIGHT = 0.4

    def __init__(self, collection):
        self.log("Initializing Ensemble Agent")
        self.specialist = SpecialistAgent()
        self.frontier = FrontierAgent(collection)
        self.preprocessor = Preprocessor()
        self.log("Ensemble Agent is ready")

    def estimate(self, description: str) -> float:
        self.log("Running Ensemble Agent - preprocessing text")
        rewrite = self.preprocessor.preprocess(description)
        self.log(f"Pre-processed text using {self.preprocessor.model_name}")

        specialist_est = self.specialist.estimate(rewrite)
        frontier_est = self.frontier.estimate(rewrite)

        combined = (
            frontier_est * self.FRONTIER_WEIGHT
            + specialist_est * self.SPECIALIST_WEIGHT
        )
        self.log(f"Ensemble Agent complete - returning ${combined:,.0f}")
        return combined
