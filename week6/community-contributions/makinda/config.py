# Week 6 fine-tuning: "The Price is Right"
# Improvements from week lessons: richer input (Day 2/3), more data + gentler LR (Day 5, results)

from pathlib import Path

_here = Path(__file__).resolve().parent
WEEK6_DIR = _here.parent.parent
REPO_ROOT = _here.parent.parent.parent

# ---------------------------------------------------------------------------
# Parameters: inputs we use to determine the price (Day 2 + Day 3 lessons)
# Day 2: structured product info (Title, Category, Description) helps the model.
# Day 3: weight and text features helped traditional ML; we include weight when present.
# We pass Title, Category, Description, and Weight (if available) as a single block.
# ---------------------------------------------------------------------------
DATASET = "ed-donner/items_lite"
TRAIN_SIZE = 100   # Day 5 used 100 train; course recommended 50–100 (we use 100 for better signal)
VAL_SIZE = 50      # Day 5 used 50 val

# ---------------------------------------------------------------------------
# Hyperparameters (Day 5 + results.ipynb lesson)
# Course fine-tuned model got 75.91 error vs 62.51 zero-shot → likely overfitting.
# Gentler learning rate and 1 epoch to avoid overfitting on small data.
# ---------------------------------------------------------------------------
BASE_MODEL = "gpt-4.1-nano-2025-04-14"
N_EPOCHS = 1
BATCH_SIZE = 1
LEARNING_RATE_MULTIPLIER = 0.5   # gentler updates than default (1.0) to reduce overfitting
SEED = 42
SUFFIX = "pricer"

EVAL_SIZE = 200

# Prompt: model sees structured product info (built in notebook) and outputs price only
USER_PROMPT = """You are a product price estimation assistant. Use ONLY the product information below to estimate the price in US dollars. Respond with just the number, 2 decimal places (e.g. 29.99). No symbol, no explanation.

Product information:
{summary}"""
