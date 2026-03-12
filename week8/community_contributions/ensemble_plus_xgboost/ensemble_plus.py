"""
Ensemble agent that adds XGBoost to the course ensemble (Frontier + Specialist + NeuralNetwork).
Weights: frontier 0.7, specialist 0.1, neural_network 0.1, xgboost 0.1.
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_week8 = os.path.abspath(os.path.join(_here, "..", ".."))
if _week8 not in sys.path:
    sys.path.insert(0, _week8)
if _here not in sys.path:
    sys.path.insert(0, _here)

from agents.agent import Agent
from agents.specialist_agent import SpecialistAgent
from agents.frontier_agent import FrontierAgent
from agents.neural_network_agent import NeuralNetworkAgent
from agents.preprocessor import Preprocessor

from xgboost_agent import XGBoostAgent


class EnsembleAgentPlus(Agent):
    """Same as course EnsembleAgent but adds XGBoost: 0.7*frontier + 0.1*specialist + 0.1*NN + 0.1*xgb."""
    name = "Ensemble Agent (+ XGBoost)"
    color = Agent.YELLOW

    def __init__(self, collection):
        self.log("Initializing Ensemble Agent (+ XGBoost)")
        self.preprocessor = Preprocessor()
        self.specialist = SpecialistAgent()
        self.frontier = FrontierAgent(collection)
        self.neural_network = NeuralNetworkAgent()
        self.xgboost = XGBoostAgent(model_path=os.path.join(_here, "xgboost_pricer.pkl"))
        self.log("Ensemble Agent (+ XGBoost) is ready")

    def price(self, description: str) -> float:
        self.log("Running Ensemble (+ XGBoost) - preprocessing text")
        rewrite = self.preprocessor.preprocess(description)
        specialist = self.specialist.price(rewrite)
        frontier = self.frontier.price(rewrite)
        neural_network = self.neural_network.price(rewrite)
        xgb = self.xgboost.price(rewrite)
        combined = frontier * 0.7 + specialist * 0.1 + neural_network * 0.1 + xgb * 0.1
        self.log(f"Ensemble (+ XGBoost) complete - returning ${combined:.2f}")
        return combined
