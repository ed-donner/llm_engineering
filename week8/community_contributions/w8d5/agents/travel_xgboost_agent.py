import os
import sys
import numpy as np
import joblib
from sentence_transformers import SentenceTransformer
import xgboost as xgb

w8d5_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if w8d5_path not in sys.path:
    sys.path.insert(0, w8d5_path)

from agents.agent import Agent


class TravelXGBoostAgent(Agent):

    name = "XGBoost Estimator"
    color = Agent.GREEN

    def __init__(self, collection):
        self.log("XGBoost Estimator initializing")
        self.collection = collection
        self.model_path = os.path.join(w8d5_path, 'helpers', 'travel_xgboost_model.pkl')
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        if os.path.exists(self.model_path):
            self.log("Loading existing XGBoost model")
            self.model = joblib.load(self.model_path)
        else:
            self.log("Training new XGBoost model")
            self.model = self._train_model()
            joblib.dump(self.model, self.model_path)
            self.log(f"XGBoost model saved to {self.model_path}")
        
        self.log("XGBoost Estimator ready")

    def _train_model(self):
        self.log("Fetching training data from ChromaDB")
        result = self.collection.get(include=['embeddings', 'metadatas'])
        
        X = np.array(result['embeddings'])
        y = np.array([m['price'] for m in result['metadatas']])
        
        self.log(f"Training on {len(X)} samples")
        
        model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X, y)
        self.log("XGBoost training complete")
        
        return model

    def estimate(self, description: str) -> float:
        self.log(f"XGBoost estimating price for: {description[:50]}...")
        
        embedding = self.embedder.encode([description])[0]
        embedding_2d = embedding.reshape(1, -1)
        
        prediction = self.model.predict(embedding_2d)[0]
        
        prediction = max(0, prediction)
        
        self.log(f"XGBoost estimate: ${prediction:.2f}")
        return float(prediction)

