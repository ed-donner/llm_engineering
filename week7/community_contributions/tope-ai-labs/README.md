# Tope AI Labs – Week 7: Fine-tune Llama 3.2 for Price Prediction

This folder contains a **small-dataset** fine-tuning pipeline for **Meta Llama 3.2** (3B) to predict product prices from descriptions, using Week 7 samples and the Hugging Face stack.

## Contents

- **`llama32_price_prediction_finetune.ipynb`** – End-to-end notebook:
  - Loads Week 7–style price data from Hugging Face (or builds a small local dataset)
  - Fine-tunes **Llama 3.2 3B** with **QLoRA** (4-bit + LoRA)
  - Uses **Hugging Face** (`transformers`, `datasets`, `peft`, `trl`)
  - Trains on a **small subset** of samples for quick runs (e.g. Colab T4)

## Data

- Uses the same format as Week 7: **“What does this cost to the nearest dollar?”** + product summary → **“Price is $X.00”**.
- Data source: `ed-donner/items_prompts_lite` (or `items_lite` + prompt building). The notebook uses a **small subset** (e.g. 2,000–5,000 samples) by default for faster iteration.

## Requirements

- GPU (e.g. T4 on Colab for small runs; A100 for larger/full data).
- Hugging Face token (for gated Llama and optional Hub push).
- Optional: `wandb` for logging.

## Quick start

1. Open `llama32_price_prediction_finetune.ipynb` in Jupyter or Colab.
2. Set `HF_TOKEN` (and optionally `WANDB_API_KEY`).
3. Run all cells; training uses QLoRA + SFTTrainer on the small dataset.
4. Optionally push the adapter to the Hub or run the Week 7 evaluator on the test set.
