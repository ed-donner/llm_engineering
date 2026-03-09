"""
Enhanced evaluation utilities for price prediction models
"""

import numpy as np
from typing import List, Callable, Optional
from tqdm import tqdm
import re
from concurrent.futures import ThreadPoolExecutor
import time


def extract_price(response: str) -> float:
    """
    Extract price from model response
    
    Args:
        response: Model response string
        
    Returns:
        Extracted price as float
    """
    if isinstance(response, (int, float)):
        return float(response)
    
    # Try to find price pattern like $XX.XX or XX.XX
    price_patterns = [
        r'\$(\d+\.?\d*)',  # $123.45
        r'(\d+\.?\d*)\s*dollars?',  # 123.45 dollars
        r'^(\d+\.?\d*)$',  # Just a number
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, str(response))
        if match:
            try:
                return float(match.group(1))
            except:
                pass
    
    # If no pattern found, try to convert directly
    try:
        return float(response)
    except:
        return 0.0


def compute_metrics(predictions: List[float], actuals: List[float]) -> dict:
    """
    Compute evaluation metrics
    
    Args:
        predictions: List of predicted prices
        actuals: List of actual prices
        
    Returns:
        Dictionary of metrics
    """
    predictions = np.array(predictions)
    actuals = np.array(actuals)
    
    # Mean Absolute Error
    mae = np.mean(np.abs(predictions - actuals))
    
    # Root Mean Squared Error
    rmse = np.sqrt(np.mean((predictions - actuals) ** 2))
    
    # Mean Absolute Percentage Error
    mape = np.mean(np.abs((predictions - actuals) / actuals)) * 100
    
    # R-squared
    ss_res = np.sum((actuals - predictions) ** 2)
    ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    # Median Absolute Error
    median_ae = np.median(np.abs(predictions - actuals))
    
    # Percentage within X% of actual
    within_10_pct = np.mean(np.abs((predictions - actuals) / actuals) < 0.10) * 100
    within_20_pct = np.mean(np.abs((predictions - actuals) / actuals) < 0.20) * 100
    
    return {
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
        'r2': r2,
        'median_ae': median_ae,
        'within_10_pct': within_10_pct,
        'within_20_pct': within_20_pct,
    }


def evaluate(predictor: Callable, 
            items: List,
            size: Optional[int] = None,
            workers: int = 1,
            show_progress: bool = True) -> dict:
    """
    Evaluate a price prediction model
    
    Args:
        predictor: Function that takes an Item and returns predicted price
        items: List of Item objects to evaluate
        size: Number of items to evaluate (None for all)
        workers: Number of parallel workers
        show_progress: Show progress bar
        
    Returns:
        Dictionary with evaluation results
    """
    if size:
        items = items[:size]
    
    predictions = []
    actuals = []
    errors = []
    
    start_time = time.time()
    
    if workers > 1:
        # Parallel evaluation
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(tqdm(
                executor.map(predictor, items),
                total=len(items),
                disable=not show_progress,
                desc="Evaluating"
            ))
    else:
        # Sequential evaluation
        results = []
        iterator = tqdm(items, disable=not show_progress, desc="Evaluating")
        for item in iterator:
            try:
                pred = predictor(item)
                results.append(pred)
            except Exception as e:
                print(f"Error predicting {item.title}: {e}")
                results.append(0.0)
    
    # Extract prices and compute errors
    for item, result in zip(items, results):
        pred_price = extract_price(result)
        actual_price = item.price
        
        predictions.append(pred_price)
        actuals.append(actual_price)
        errors.append(abs(pred_price - actual_price))
    
    elapsed_time = time.time() - start_time
    
    # Compute metrics
    metrics = compute_metrics(predictions, actuals)
    
    # Add timing info
    metrics['total_time'] = elapsed_time
    metrics['time_per_item'] = elapsed_time / len(items)
    metrics['items_evaluated'] = len(items)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"EVALUATION RESULTS")
    print(f"{'='*60}")
    print(f"Items evaluated: {len(items)}")
    print(f"Mean Absolute Error (MAE): ${metrics['mae']:.2f}")
    print(f"Root Mean Squared Error (RMSE): ${metrics['rmse']:.2f}")
    print(f"Median Absolute Error: ${metrics['median_ae']:.2f}")
    print(f"Mean Absolute Percentage Error (MAPE): {metrics['mape']:.2f}%")
    print(f"R-squared: {metrics['r2']:.4f}")
    print(f"Within 10% of actual: {metrics['within_10_pct']:.1f}%")
    print(f"Within 20% of actual: {metrics['within_20_pct']:.1f}%")
    print(f"Time: {elapsed_time:.2f}s ({metrics['time_per_item']:.3f}s per item)")
    print(f"{'='*60}\n")
    
    return metrics


def compare_models(models: dict, items: List, size: Optional[int] = None) -> dict:
    """
    Compare multiple models
    
    Args:
        models: Dictionary of {model_name: predictor_function}
        items: List of items to evaluate
        size: Number of items to evaluate
        
    Returns:
        Dictionary of results for each model
    """
    results = {}
    
    for name, predictor in models.items():
        print(f"\n{'#'*60}")
        print(f"Evaluating: {name}")
        print(f"{'#'*60}")
        
        metrics = evaluate(predictor, items, size=size)
        results[name] = metrics
    
    # Print comparison
    print(f"\n{'='*60}")
    print(f"MODEL COMPARISON")
    print(f"{'='*60}")
    print(f"{'Model':<30} {'MAE':<12} {'RMSE':<12} {'R²':<8}")
    print(f"{'-'*60}")
    
    for name, metrics in results.items():
        print(f"{name:<30} ${metrics['mae']:<11.2f} ${metrics['rmse']:<11.2f} {metrics['r2']:<7.4f}")
    
    print(f"{'='*60}\n")
    
    return results


class UncertaintyQuantifier:
    """
    Quantify prediction uncertainty using multiple forward passes
    """
    
    def __init__(self, predictor: Callable, n_samples: int = 10):
        """
        Args:
            predictor: Prediction function
            n_samples: Number of samples for uncertainty estimation
        """
        self.predictor = predictor
        self.n_samples = n_samples
    
    def predict_with_uncertainty(self, item) -> tuple:
        """
        Predict with uncertainty estimation
        
        Returns:
            (mean_prediction, std_prediction, confidence_interval)
        """
        predictions = []
        
        for _ in range(self.n_samples):
            pred = extract_price(self.predictor(item))
            predictions.append(pred)
        
        mean_pred = np.mean(predictions)
        std_pred = np.std(predictions)
        
        # 95% confidence interval
        ci_lower = mean_pred - 1.96 * std_pred
        ci_upper = mean_pred + 1.96 * std_pred
        
        return mean_pred, std_pred, (ci_lower, ci_upper)
