"""
XGBoost pricer agent: predicts price from product description using embeddings + XGBRegressor.
Train with train_xgboost.py; saves xgboost_pricer.pkl in this directory.
"""
import os
import logging
from sentence_transformers import SentenceTransformer
import joblib

# Allow import when run from week8 (agents.*) or from this folder
try:
    from agents.agent import Agent
except ImportError:
    import sys
    _week8 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if _week8 not in sys.path:
        sys.path.insert(0, _week8)
    from agents.agent import Agent

MODEL_FILENAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xgboost_pricer.pkl")
ENCODER_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class XGBoostAgent(Agent):
    name = "XGBoost Agent"
    color = Agent.CYAN

    def __init__(self, model_path: str = None):
        self.log("Initializing XGBoost Agent")
        self.model_path = model_path or MODEL_FILENAME
        if not os.path.isfile(self.model_path):
            raise FileNotFoundError(
                f"Model not found: {self.model_path}\n"
                "Run train_xgboost.py from this directory first to create it."
            )
        self.encoder = SentenceTransformer(ENCODER_NAME)
        self.model = joblib.load(self.model_path)
        self.log("XGBoost Agent is ready")

    def price(self, description: str) -> float:
        self.log("XGBoost Agent is predicting")
        vec = self.encoder.encode([description])
        pred = self.model.predict(vec)[0]
        result = max(0.0, float(pred))
        self.log(f"XGBoost Agent completed - predicting ${result:.2f}")
        return result
