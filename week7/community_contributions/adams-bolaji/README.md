# Multi-Task Pricer 

**Author:** adams-bolaji  
**Week 7 Community Contribution** — Extends "The Price Is Right" capstone with multi-task prediction.

## Overview

This project fine-tunes an open-source LLM (e.g., Llama 3.2) to predict **both** product category and price from a description in a single completion, using QLoRA.

**Format:** `Category: <category>. Price is $<number>.00`

### Files

| File | Description |
|------|-------------|
| `multitask_utils.py` | Prompt/completion builders, parsers, and evaluation helpers |
| `multitask_pricer.ipynb` | End-to-end flow: data prep → training → evaluation |
| `README.md` | This file |

## Setup

### 1. Environment

From the repo root or `week7/community_contributions/adams-bolaji/`:

```bash
pip install datasets transformers torch peft bitsandbytes trl accelerate python-dotenv tqdm matplotlib scikit-learn plotly
```

### 3. Path Setup (Local)

The notebook adds `week7` to `sys.path` so `pricer` can be imported. Run from repo root, or adjust `find_week7_root()` if needed.

## Usage

### Data Preparation

- Load items from `ed-donner/items_lite` or `ed-donner/items_full`
- Build multi-task prompts: question + summary + `Category: `
- Completions: `Category: X. Price is $Y.00`
- Optionally push to HuggingFace Hub for Colab training

### Training 

- Use **Google Colab** (T4/A100) for QLoRA fine-tuning
- Copy the training cells and set:
  - `DATASET_NAME` → your multitask dataset or use in-notebook data
  - `HF_USER` → your HuggingFace username
  - `BASE_MODEL` → `meta-llama/Llama-3.2-3B` (or 1B for faster runs)
- Training time: ~1–2+ hours depending on data size and GPU

### Evaluation (Day 5)

- Load base model + PEFT adapter
- Run `MultiTaskEvaluator` for:
  - **Price:** MAE, MSE, R²
  - **Category:** accuracy (exact match, normalized)
- Plots: predicted vs actual price, error trend

## Multi-Task vs Single-Task

| Aspect | Single-Task (Week 7) | Multi-Task (This Project) |
|--------|----------------------|---------------------------|
| Output | Price only | Category + Price |
| Completion | `Price is $99.00` | `Electronics. Price is $99.00` |
| Metrics | MAE, R² | MAE, R² + category accuracy |
| Complexity | Lower | Higher (longer completions) |
