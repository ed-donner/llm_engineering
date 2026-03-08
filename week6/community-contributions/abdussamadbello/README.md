# Week 6 – Product Pricer Fine-Tuning (abdussamadbello)

This contribution implements **Day 5** of the “Price is Right” capstone: fine-tuning a frontier model (GPT-4.1-nano) on the product-pricer dataset and evaluating it.

## What’s included

- **`week6-assignment.ipynb`** – End-to-end fine-tuning notebook:
  - Load train/val/test from Hugging Face (`ed-donner/items_full` or `items_lite`).
  - Build JSONL in the format required by the OpenAI fine-tuning API.
  - Upload training and validation files (using `pathlib.Path` for SDK compatibility).
  - Create a fine-tuning job and poll until complete.
  - Run inference with the fine-tuned model and evaluate with the shared `evaluate()` metric.
  - **Baseline comparison**: run base (non–fine-tuned) GPT-4.1-nano on the same test subset and report mean absolute error vs fine-tuned.
  - **Category-stratified eval**: break down mean absolute error by product category (Electronics, Home, etc.); show a table and bar chart (baseline vs fine-tuned per category).
  - **Reasons**: short notes on why some categories do better/worse (scale, sample size, where fine-tuning helps), plus an optional cell that asks the base model for a one-sentence reason (“Why might this product cost around $X?”).

The notebook uses explicit **OpenAI client setup** (API key and base URL from env) and **Path-based file uploads** so it works with current OpenAI SDK behaviour and avoids proxy/upload issues when `OPENAI_BASE_URL` is unset or points at OpenAI.

## Setup

Run from the **repository root** so the `pricer` package is importable:

```bash
cd /path/to/llm_engineering
# Optional: create venv and install deps
pip install openai python-dotenv huggingface_hub
```

Create a `.env` in the repo root (do not commit it):

```bash
HF_TOKEN=hf_...
OPENAI_API_KEY=sk-...
# Omit OPENAI_BASE_URL or set to https://api.openai.com/v1 for fine-tuning
```

## How to run

1. From repo root, open `week6/community-contributions/abdussamadbello/week6-assignment.ipynb`.
2. Run all cells in order. The notebook will:
   - Load data from Hugging Face (requires `HF_TOKEN`).
   - Write `jsonl/fine_tune_train.jsonl` and `jsonl/fine_tune_validation.jsonl` under the notebook’s working directory (create `jsonl/` if needed).
   - Upload files to OpenAI and start a fine-tuning job.
   - Evaluate the fine-tuned model on the test set and report the metric.

For a quick, low-cost run, keep the default small slice (e.g. 100 train / 50 val). Increase dataset size in the notebook if desired.

## Notes

- **File upload**: The OpenAI Python SDK expects the `file` argument to be a `PathLike`, file-like object, or bytes—not a plain string. The notebook uses `pathlib.Path("jsonl/...")` for compatibility.
- **Base URL**: Fine-tuning is only supported on OpenAI’s API. If you use a proxy (e.g. OpenRouter), unset `OPENAI_BASE_URL` or set it to `https://api.openai.com/v1` for this notebook.
- **Evaluation**: Uses the same `evaluate()` from `pricer.evaluator` as the main week 6 material.
