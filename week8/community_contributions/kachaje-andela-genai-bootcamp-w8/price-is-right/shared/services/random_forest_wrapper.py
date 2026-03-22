import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import os
import re
import pickle
import threading
import gzip
import warnings
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import joblib
from agents.agent import Agent

# Suppress scikit-learn version mismatch warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

class RandomForestAgentWrapper(Agent):
    name = "Random Forest Agent"
    color = Agent.MAGENTA
    
    def __init__(self):
        self.log("Random Forest Agent is initializing")
        self._model_loaded = False
        self._model_lock = threading.Lock()
        self.model: Optional[object] = None
        
        try:
            self.log("Loading sentence transformer model...")
            self.vectorizer = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            self.log("Sentence transformer loaded successfully")
            
            # Load model in background thread for faster startup
            self._load_model_async()
            self.log("Random Forest Agent is ready (model loading in background)")
        except Exception as e:
            self.log(f"Error initializing Random Forest Agent: {str(e)}")
            raise
    
    def _load_model_async(self):
        """Load the model in a background thread"""
        def load_model():
            try:
                self.log("Loading random forest model...")
                # Use absolute path to ensure we find the model file
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                model_path = os.path.join(base_dir, 'data', 'models', 'random_forest_model.pkl')
                self.log(f"Looking for model at: {model_path}")
                
                # Check if file exists
                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"Model file not found at {model_path}")
                
                # Try to load compressed model first, fallback to regular model
                compressed_path = os.path.join(base_dir, 'data', 'models', 'random_forest_model_compressed.pkl.gz')
                
                if os.path.exists(compressed_path):
                    self.log(f"Loading compressed model from: {compressed_path}")
                    with gzip.open(compressed_path, 'rb') as f:
                        self.model = joblib.load(f)
                else:
                    self.log(f"Loading regular model from: {model_path}")
                    # Note: Model was trained with scikit-learn 1.5.2, current version is 1.7.2
                    # This may cause warnings but the model should still work correctly
                    # Use joblib with memory mapping for faster loading
                    self.model = joblib.load(model_path, mmap_mode='r')
                
                with self._model_lock:
                    self._model_loaded = True
                
                self.log("Random Forest model loaded successfully")
            except Exception as e:
                self.log(f"Error loading model: {str(e)}")
                # Don't raise the exception to prevent service startup failure
                # The service can still start and handle requests gracefully
                import traceback
                self.log(f"Model loading traceback: {traceback.format_exc()}")
        
        # Start loading in background thread
        thread = threading.Thread(target=load_model, daemon=True)
        thread.start()
    
    def _ensure_model_loaded(self):
        """Ensure model is loaded before use"""
        if not self._model_loaded:
            self.log("Waiting for model to load...")
            # Wait for model to be loaded
            while not self._model_loaded:
                import time
                time.sleep(0.1)

    def price(self, description: str) -> float:
        self.log("Random Forest Agent is starting a prediction")
        
        # Ensure model is loaded before use
        self._ensure_model_loaded()
        
        # Check if model is actually loaded
        if self.model is None:
            self.log("Model is not available, returning default price")
            return 0.0
        
        try:
            vector = self.vectorizer.encode([description])
            result = max(0, self.model.predict(vector)[0])
            self.log(f"Random Forest Agent completed - predicting ${result:.2f}")
            return result
        except Exception as e:
            self.log(f"Error during prediction: {str(e)}")
            return 0.0
