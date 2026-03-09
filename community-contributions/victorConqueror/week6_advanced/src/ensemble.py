"""
Ensemble model combining multiple predictors
"""

import numpy as np
from typing import List, Callable, Dict
import pandas as pd


class EnsemblePredictor:
    """
    Ensemble predictor that combines multiple models
    """
    
    def __init__(self, models: Dict[str, Callable], weights: Dict[str, float] = None):
        """
        Initialize ensemble
        
        Args:
            models: Dictionary of {model_name: predictor_function}
            weights: Dictionary of {model_name: weight}. If None, uses equal weights
        """
        self.models = models
        
        if weights is None:
            # Equal weights
            n = len(models)
            self.weights = {name: 1.0/n for name in models.keys()}
        else:
            # Normalize weights
            total = sum(weights.values())
            self.weights = {name: w/total for name, w in weights.items()}
        
        print(f"Ensemble initialized with {len(models)} models")
        print(f"Weights: {self.weights}")
    
    def predict(self, item, **kwargs) -> float:
        """
        Make ensemble prediction
        
        Args:
            item: Item to predict
            **kwargs: Additional arguments for individual models
            
        Returns:
            Weighted average prediction
        """
        predictions = {}
        
        for name, model in self.models.items():
            try:
                pred = model(item, **kwargs)
                predictions[name] = float(pred)
            except Exception as e:
                print(f"Error in model {name}: {e}")
                predictions[name] = 0.0
        
        # Weighted average
        ensemble_pred = sum(predictions[name] * self.weights[name] 
                          for name in self.models.keys())
        
        return max(0, ensemble_pred)  # Ensure non-negative
    
    def predict_batch(self, items: List, **kwargs) -> np.ndarray:
        """
        Make predictions for multiple items
        
        Args:
            items: List of items
            **kwargs: Additional arguments
            
        Returns:
            Array of predictions
        """
        predictions = [self.predict(item, **kwargs) for item in items]
        return np.array(predictions)
    
    def get_individual_predictions(self, item, **kwargs) -> Dict[str, float]:
        """
        Get predictions from each individual model
        
        Args:
            item: Item to predict
            **kwargs: Additional arguments
            
        Returns:
            Dictionary of {model_name: prediction}
        """
        predictions = {}
        
        for name, model in self.models.items():
            try:
                pred = model(item, **kwargs)
                predictions[name] = float(pred)
            except Exception as e:
                print(f"Error in model {name}: {e}")
                predictions[name] = 0.0
        
        return predictions


class StackedEnsemble:
    """
    Stacked ensemble with meta-learner
    """
    
    def __init__(self, base_models: Dict[str, Callable], meta_model):
        """
        Initialize stacked ensemble
        
        Args:
            base_models: Dictionary of base models
            meta_model: Meta-learner model (e.g., XGBoost, Linear Regression)
        """
        self.base_models = base_models
        self.meta_model = meta_model
        self.is_fitted = False
    
    def fit(self, items: List, prices: np.ndarray, **kwargs):
        """
        Train the meta-learner
        
        Args:
            items: Training items
            prices: Target prices
            **kwargs: Additional arguments for base models
        """
        # Get predictions from base models
        base_predictions = []
        
        for name, model in self.base_models.items():
            print(f"Getting predictions from {name}...")
            preds = [model(item, **kwargs) for item in items]
            base_predictions.append(preds)
        
        # Stack predictions as features
        X_meta = np.column_stack(base_predictions)
        
        # Train meta-model
        print("Training meta-learner...")
        self.meta_model.fit(X_meta, prices)
        
        self.is_fitted = True
        print("✅ Stacked ensemble trained!")
    
    def predict(self, item, **kwargs) -> float:
        """
        Make stacked prediction
        
        Args:
            item: Item to predict
            **kwargs: Additional arguments
            
        Returns:
            Meta-model prediction
        """
        if not self.is_fitted:
            raise ValueError("Ensemble must be fitted before prediction")
        
        # Get base predictions
        base_preds = []
        for model in self.base_models.values():
            pred = model(item, **kwargs)
            base_preds.append(float(pred))
        
        # Meta-model prediction
        X_meta = np.array(base_preds).reshape(1, -1)
        meta_pred = self.meta_model.predict(X_meta)[0]
        
        return max(0, float(meta_pred))
    
    def predict_batch(self, items: List, **kwargs) -> np.ndarray:
        """
        Make predictions for multiple items
        
        Args:
            items: List of items
            **kwargs: Additional arguments
            
        Returns:
            Array of predictions
        """
        predictions = [self.predict(item, **kwargs) for item in items]
        return np.array(predictions)


def create_simple_ensemble(xgb_model, nn_model, rag_baseline,
                          weight_xgb=0.4, weight_nn=0.4, weight_rag=0.2):
    """
    Create a simple weighted ensemble
    
    Args:
        xgb_model: XGBoost model
        nn_model: Neural network model
        rag_baseline: RAG baseline predictor
        weight_xgb: Weight for XGBoost
        weight_nn: Weight for neural network
        weight_rag: Weight for RAG baseline
        
    Returns:
        EnsemblePredictor
    """
    models = {
        'xgboost': xgb_model,
        'neural_net': nn_model,
        'rag': rag_baseline
    }
    
    weights = {
        'xgboost': weight_xgb,
        'neural_net': weight_nn,
        'rag': weight_rag
    }
    
    return EnsemblePredictor(models, weights)
