#!/usr/bin/env python3
"""
Train a LinearRegression ensemble over Specialist, Frontier, and RF predictions.
Saves to ensemble_model.pkl and logs coefficients and metrics.
"""

import argparse
import random
import joblib
import pandas as pd
import chromadb
from tqdm import tqdm

from agents.specialist_agent import SpecialistAgent
from agents.frontier_agent import FrontierAgent
from agents.random_forest_agent import RandomForestAgent

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

from logging_utils import init_logger
import config as cfg

logger = init_logger("DealIntel.TrainEnsemble")

def main():
    parser = argparse.ArgumentParser(description="Train Ensemble LinearRegression")
    parser.add_argument("--sample-size", type=int, default=cfg.ENSEMBLE_SAMPLE_SIZE)
    args = parser.parse_args()

    logger.info("Initializing Chroma collection")
    client = chromadb.PersistentClient(path=cfg.DB_PATH)
    collection = client.get_or_create_collection(cfg.COLLECTION_NAME)

    logger.info("Loading datapoints")
    result = collection.get(include=['documents', 'metadatas'], limit=args.sample_size * 10)
    documents = result["documents"]
    metadatas = result["metadatas"]
    if not documents:
        raise RuntimeError("No documents in collection — build the vector store first.")

    pairs = list(zip(documents, metadatas))
    random.seed(42)
    random.shuffle(pairs)
    pairs = pairs[:args.sample_size]

    logger.info("Initializing agents")
    specialist = SpecialistAgent()
    frontier = FrontierAgent(collection)
    rf = RandomForestAgent()

    X_rows = []
    y_vals = []
    logger.info(f"Collecting predictions for {len(pairs)} samples")
    for doc, md in tqdm(pairs, desc="Collect"):
        description = doc
        target_price = float(md["price"])

        try:
            s = specialist.price(description)
        except Exception as e:
            logger.warning(f"Specialist failed; skipping sample: {e}")
            continue

        try:
            f = frontier.price(description)
        except Exception as e:
            logger.warning(f"Frontier failed; skipping sample: {e}")
            continue

        try:
            r = rf.price(description)
        except Exception as e:
            logger.warning(f"RF failed; skipping sample: {e}")
            continue

        X_rows.append({
            "Specialist": s,
            "Frontier": f,
            "RandomForest": r,
            "Min": min(s, f, r),
            "Max": max(s, f, r),
        })
        y_vals.append(target_price)

    if len(X_rows) < 20:
        raise RuntimeError("Too few samples collected. Ensure tokens/services are configured and retry.")

    X = pd.DataFrame(X_rows)
    y = pd.Series(y_vals)

    logger.info("Fitting LinearRegression")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    lr = LinearRegression()
    lr.fit(X_train, y_train)

    preds = lr.predict(X_test)
    rmse = mean_squared_error(y_test, preds, squared=False)
    r2 = r2_score(y_test, preds)
    logger.info(f"Holdout RMSE={rmse:.2f}, R2={r2:.3f}")

    coef_log = ", ".join([f"{col}={coef:.3f}" for col, coef in zip(X.columns.tolist(), lr.coef_)])
    logger.info(f"Coefficients: {coef_log}; Intercept={lr.intercept_:.3f}")

    joblib.dump(lr, "ensemble_model.pkl")
    logger.info("Saved model to ensemble_model.pkl")

if __name__ == "__main__":
    main()