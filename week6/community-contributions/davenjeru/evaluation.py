"""Evaluation metrics and Weights & Biases integration."""
import numpy as np
import wandb
from sklearn.metrics import mean_absolute_error, mean_squared_error

WANDB_PROJECT = "llama-3.2-housing-pricer"


def init_wandb(config: dict, run_name: str = None):
    """Initialize W&B run.
    
    Args:
        config: Configuration dictionary to log
        run_name: Optional name for the run
    """
    wandb.init(project=WANDB_PROJECT, name=run_name, config=config)


def compute_metrics(y_true, y_pred) -> dict:
    """Compute MAE, RMSE, MAPE.
    
    Args:
        y_true: Actual prices
        y_pred: Predicted prices
        
    Returns:
        Dictionary with mae, rmse, mape keys
    """
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    mask = y_true != 0
    if mask.sum() > 0:
        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    else:
        mape = 0.0
    
    return {
        "mae": mae,
        "rmse": rmse,
        "mape": mape
    }


def log_model_results(model_name: str, y_true, y_pred):
    """Log metrics, predictions table, and scatter plot to W&B.
    
    Args:
        model_name: Name of the model for labeling
        y_true: Actual prices
        y_pred: Predicted prices
        
    Returns:
        Dictionary with computed metrics
    """
    metrics = compute_metrics(y_true, y_pred)
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    
    wandb.log({
        f"{model_name}/mae": metrics["mae"],
        f"{model_name}/rmse": metrics["rmse"],
        f"{model_name}/mape": metrics["mape"]
    })
    
    table_data = []
    for a, p in zip(y_true, y_pred):
        error = abs(a - p)
        pct_error = (error / a * 100) if a != 0 else 0
        table_data.append([float(a), float(p), float(error), float(pct_error)])
    
    table = wandb.Table(
        columns=["actual", "predicted", "error", "pct_error"],
        data=table_data
    )
    wandb.log({f"{model_name}/predictions": table})
    
    wandb.log({
        f"{model_name}/scatter": wandb.plot.scatter(
            table, "actual", "predicted", 
            title=f"{model_name}: Actual vs Predicted"
        )
    })
    
    return metrics


def log_training_step(epoch: int, train_loss: float, val_loss: float = None):
    """Log training progress to W&B.
    
    Args:
        epoch: Current epoch number
        train_loss: Training loss value
        val_loss: Optional validation loss value
    """
    log_dict = {"epoch": epoch, "train_loss": train_loss}
    if val_loss is not None:
        log_dict["val_loss"] = val_loss
    wandb.log(log_dict)


def create_comparison_table(results: list[dict]):
    """Create final model comparison table in W&B.
    
    Args:
        results: List of dicts with keys: name, type, mae, rmse, mape
    """
    table = wandb.Table(
        columns=["Model", "Type", "MAE", "RMSE", "MAPE"],
        data=[
            [r["name"], r["type"], r["mae"], r["rmse"], r["mape"]] 
            for r in results
        ]
    )
    wandb.log({"model_comparison": table})


def create_comparison_charts(results: list[dict]):
    """Create bar charts comparing all models by MAE, RMSE, and MAPE.
    
    Args:
        results: List of dicts with keys: name, type, mae, rmse, mape
    """
    sorted_by_mae = sorted(results, key=lambda r: r["mae"])
    
    mae_table = wandb.Table(
        columns=["Model", "MAE ($)"],
        data=[[r["name"], r["mae"]] for r in sorted_by_mae]
    )
    wandb.log({
        "comparison/mae_chart": wandb.plot.bar(
            mae_table, "Model", "MAE ($)", 
            title="Model Comparison: MAE (lower is better)"
        )
    })
    
    sorted_by_rmse = sorted(results, key=lambda r: r["rmse"])
    rmse_table = wandb.Table(
        columns=["Model", "RMSE ($)"],
        data=[[r["name"], r["rmse"]] for r in sorted_by_rmse]
    )
    wandb.log({
        "comparison/rmse_chart": wandb.plot.bar(
            rmse_table, "Model", "RMSE ($)", 
            title="Model Comparison: RMSE (lower is better)"
        )
    })
    
    sorted_by_mape = sorted(results, key=lambda r: r["mape"])
    mape_table = wandb.Table(
        columns=["Model", "MAPE (%)"],
        data=[[r["name"], r["mape"]] for r in sorted_by_mape]
    )
    wandb.log({
        "comparison/mape_chart": wandb.plot.bar(
            mape_table, "Model", "MAPE (%)", 
            title="Model Comparison: MAPE (lower is better)"
        )
    })
