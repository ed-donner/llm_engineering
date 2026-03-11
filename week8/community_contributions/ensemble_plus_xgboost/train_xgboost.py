"""
Train XGBoost on (embedding of product summary -> price) using course data.
Saves xgboost_pricer.pkl in this directory. Run from anywhere:

  uv run python week8/community_contributions/ensemble_plus_xgboost/train_xgboost.py
  # or from inside the ensemble folder:
  uv run python train_xgboost.py

Requires: HF_TOKEN, items_lite on HuggingFace.
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_week8 = os.path.abspath(os.path.join(_here, "..", ".."))
if _week8 not in sys.path:
    sys.path.insert(0, _week8)

from dotenv import load_dotenv
# Load .env from this dir, week8, or repo root (whichever exists)
for _d in [_here, _week8, os.path.join(_week8, "..")]:
    _env = os.path.join(_d, ".env")
    if os.path.isfile(_env):
        load_dotenv(_env, override=True)
        break
else:
    load_dotenv(override=True)  # fallback: cwd

from huggingface_hub import login
from sentence_transformers import SentenceTransformer
import joblib

load_dotenv(override=True)
login(token=os.environ.get("HF_TOKEN", ""), add_to_git_credential=False)
from agents.items import Item

DATASET = "ed-donner/items_lite"
ENCODER_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_PATH = os.path.join(_here, "xgboost_pricer.pkl")
TRAIN_SIZE = 10_000  # subset for speed; use None for full

def main():
    import xgboost as xgb
    from tqdm import tqdm

    print("Loading data...")
    train, _val, _test = Item.from_hub(DATASET)
    if TRAIN_SIZE:
        train = train[:TRAIN_SIZE]
    print(f"Training on {len(train)} items")

    print("Loading encoder...")
    encoder = SentenceTransformer(ENCODER_NAME)

    print("Encoding summaries...")
    texts = [item.summary or item.title for item in train]
    X = encoder.encode(texts, show_progress_bar=True)
    y = [item.price for item in train]

    print("Training XGBRegressor...")
    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)

    os.makedirs(os.path.dirname(MODEL_PATH) or ".", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Saved to {MODEL_PATH}")

if __name__ == "__main__":
    main()
