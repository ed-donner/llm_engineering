import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

from agents.specialist_agent import SpecialistAgent
from agents.frontier_agent import FrontierAgent
from agents.random_forest_agent import RandomForestAgent

class EnsembleAgent:

    def __init__(self, collection):
        self.specialist = SpecialistAgent()
        self.frontier = FrontierAgent(collection)
        self.random_forest = RandomForestAgent()
        self.model = joblib.load('ensemble_model.pkl')

    def price(self, description):
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
        y = self.model.predict(X)
        return y[0]