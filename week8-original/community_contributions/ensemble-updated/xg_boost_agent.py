# imports

import os
import re
from typing import List
from sentence_transformers import SentenceTransformer
import joblib
from agents.agent import Agent
import xgboost as xgb




class XGBoostAgent(Agent):

    name = "XG Boost Agent"
    color = Agent.BRIGHT_MAGENTA

    def __init__(self):
        """
        Initialize this object by loading in the saved model weights
        and the SentenceTransformer vector encoding model
        """
        self.log("XG Boost Agent is initializing")
        self.vectorizer = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.model = joblib.load('xg_boost_model.pkl')
        self.log("XG Boost Agent is ready")

    def price(self, description: str) -> float:
        """
        Use an XG Boost model to estimate the price of the described item
        :param description: the product to be estimated
        :return: the price as a float
        """        
        self.log("XG Boost Agent is starting a prediction")
        vector = self.vectorizer.encode([description])
        vector = vector.reshape(1, -1)
        # Convert the vector to DMatrix
        dmatrix = xgb.DMatrix(vector)
        # Predict the price using the model
        result = max(0, self.model.predict(dmatrix)[0])
        self.log(f"XG Boost Agent completed - predicting ${result:.2f}")
        return result



