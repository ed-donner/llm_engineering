import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib
import os

from agents.agent import Agent
from agents.specialist_agent import SpecialistAgent
from agents.frontier_agent import FrontierAgent
from agents.random_forest_agent import RandomForestAgent

class EnsembleAgent(Agent):

    name = "Ensemble Agent"
    color = Agent.YELLOW
    
    def __init__(self, collection):
        """
        Create an instance of Ensemble, by creating each of the models
        And loading the weights of the Ensemble
        """
        self.log("Initializing Ensemble Agent")
        self.specialist = SpecialistAgent()
        self.frontier = FrontierAgent(collection)
        self.random_forest = RandomForestAgent()
        # Resolve model path: prefer local contribution folder copy, fallback to week8 root
        candidate_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ensemble_model.pkl'),  # ../../ensemble_model.pkl
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ensemble_model.pkl'),  # ../../../ensemble_model.pkl (week8 root)
            'ensemble_model.pkl',
        ]
        model_path = next((p for p in candidate_paths if os.path.exists(p)), candidate_paths[-1])
        self.model = joblib.load(model_path)
        self.log("Ensemble Agent is ready")

    def price(self, description: str) -> float:
        """
        Run this ensemble model
        Ask each of the models to price the product
        Then use the Linear Regression model to return the weighted price
        :param description: the description of a product
        :return: an estimate of its price
        """
        self.log("Running Ensemble Agent - collaborating with specialist, frontier and random forest agents")
        specialist = self.specialist.price(description)
        frontier = self.frontier.price(description)
        random_forest = self.random_forest.price(description)
        X = pd.DataFrame({
            'Specialist': [specialist],
            'Frontier': [frontier],
            'RandomForest': [random_forest],
            'Min': [min(specialist, frontier, random_forest)],
            'Max': [max(specialist, frontier, random_forest)],
        })
        y = max(0, self.model.predict(X)[0])
        self.log(f"Ensemble Agent complete - returning ${y:.2f}")
        return y

