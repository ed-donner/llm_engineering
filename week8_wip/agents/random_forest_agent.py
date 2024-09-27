# imports

import os
import re
from typing import List
from sentence_transformers import SentenceTransformer
import joblib


class RandomForestAgent:

    def __init__(self):
        self.vectorizer = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.model = joblib.load('random_forest_model.pkl')

    def price(self, description: str) -> float:
        vector = self.vectorizer.encode([description])
        return max(0, self.model.predict(vector)[0])