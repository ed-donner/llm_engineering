#!/usr/bin/env python3
"""
Train a RandomForestRegressor on embeddings from ChromaDB, save to random_forest_model.pkl.
Logs simple holdout metrics.
"""

import argparse
import joblib
import numpy as np
import chromadb
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

from logging_utils import init_logger
import config as cfg

logger = init_logger("DealIntel.TrainRF")

def main():
    parser = argparse.ArgumentParser(description="Train Random Forest pricer")
    parser.add_argument("--max-datapoints", type=int, default=cfg.RF_MAX_DATAPOINTS)
    args = parser.parse_args()

    logger.info(f"Loading embeddings from {cfg.DB_PATH}/{cfg.COLLECTION_NAME} (limit={args.max_datapoints})")
    client = chromadb.PersistentClient(path=cfg.DB_PATH)
    collection = client.get_or_create_collection(cfg.COLLECTION_NAME)
    result = collection.get(include=['embeddings', 'metadatas'], limit=args.max_datapoints)

    if not result.get("embeddings"):
        raise RuntimeError("No embeddings found — build the vector store first.")

    X = np.array(result["embeddings"])
    y = np.array([md["price"] for md in result["metadatas"]])

    logger.info(f"Training RF on {X.shape[0]} samples, {X.shape[1]} features")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    rf = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)

    preds = rf.predict(X_test)
    rmse = mean_squared_error(y_test, preds, squared=False)
    r2 = r2_score(y_test, preds)
    logger.info(f"Holdout RMSE={rmse:.2f}, R2={r2:.3f}")

    joblib.dump(rf, "random_forest_model.pkl")
    logger.info("Saved model to random_forest_model.pkl")

if __name__ == "__main__":
    main()