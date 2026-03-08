"""Housing Pricer - USA Real Estate Price Prediction using ML and LLMs."""

from .data import load_raw_data, filter_data, create_splits, PRICE_MIN, PRICE_MAX
from .prompts import create_description, format_for_inference, format_for_finetuning, SYSTEM_PROMPT
from .models import (
    RandomPricer, MeanPricer,
    train_linear_regression, train_random_forest, train_xgboost,
    HousePriceMLP, parse_price, predict_with_llm
)
from .evaluation import (
    init_wandb, compute_metrics, log_model_results,
    log_training_step, create_comparison_table, create_comparison_charts, WANDB_PROJECT
)

__all__ = [
    "load_raw_data", "filter_data", "create_splits", "PRICE_MIN", "PRICE_MAX",
    "create_description", "format_for_inference", "format_for_finetuning", "SYSTEM_PROMPT",
    "RandomPricer", "MeanPricer", "train_linear_regression", "train_random_forest",
    "train_xgboost", "HousePriceMLP", "parse_price", "predict_with_llm",
    "init_wandb", "compute_metrics", "log_model_results", "log_training_step",
    "create_comparison_table", "create_comparison_charts", "WANDB_PROJECT"
]
