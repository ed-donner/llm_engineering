# imports

import os
import re
from typing import List
from sentence_transformers import SentenceTransformer
import joblib
import os
from agents.agent import Agent



class RandomForestAgent(Agent):

    name = "Random Forest Agent"
    color = Agent.MAGENTA

    def __init__(self):
        """
        Initialize this object by loading in the saved model weights
        and the SentenceTransformer vector encoding model
        """
        self.log("Random Forest Agent is initializing")
        self.vectorizer = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        # Resolve model path: prefer local contribution folder copy, fallback to week8 root
        candidate_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'random_forest_model.pkl'),  # ../../random_forest_model.pkl
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'random_forest_model.pkl'),  # ../../../random_forest_model.pkl (week8 root)
            'random_forest_model.pkl',
        ]
        model_path = next((p for p in candidate_paths if os.path.exists(p)), candidate_paths[-1])
        self.model = joblib.load(model_path)
        self.log("Random Forest Agent is ready")

    def price(self, description: str) -> float:
        """
        Use a Random Forest model to estimate the price of the described item
        :param description: the product to be estimated
        :return: the price as a float
        """        
        self.log("Random Forest Agent is starting a prediction")
        vector = self.vectorizer.encode([description])
        result = max(0, self.model.predict(vector)[0])
        self.log(f"Random Forest Agent completed - predicting ${result:.2f}")
        return result

