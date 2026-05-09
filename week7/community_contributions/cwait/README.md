# cwait / Igniters – Week 7: Fine-tune Llama 3.2 for Price Prediction

This folder contains a **small-dataset** fine-tuning pipeline for **Meta Llama 3.2 1B** to predict product prices from descriptions, using the Week 7 course data and the Hugging Face stack (QLoRA + SFTTrainer).

## Contents

- **`cwait-igniters-week7.ipynb`** – Single end-to-end notebook:
  - Loads Week 7 prompt data from Hugging Face (`ed-donner/items_prompts_lite`) and uses a **small subset** (e.g. 1,500 train / 200 val) for quick runs.
  - Fine-tunes **Llama 3.2 1B** with **QLoRA** (4-bit + LoRA).
  - Uses **Hugging Face** (`transformers`, `datasets`, `peft`, `trl`).
  - Saves the adapter locally; optionally runs the Week 7 evaluator (`util.evaluate`) on the test set.

## Data

- Same format as Week 7: **"What does this cost to the nearest dollar?"** + product summary → **"Price is $X.00"**.
- Source: `ed-donner/items_prompts_lite`. The notebook uses a small subset by default so it runs in a reasonable time on a single GPU (e.g. Colab T4).

## Requirements

- GPU (e.g. T4 on Colab for small runs).
- Hugging Face token (for gated Llama and optional Hub push).
- Optional: `wandb` for logging (currently disabled in the notebook).

## Quick start

1. Open `cwait-igniters-week7.ipynb` in Jupyter or Colab.
2. Set `HF_TOKEN` in the environment or enter it when prompted.
3. Run all cells; training uses QLoRA + SFTTrainer on the small subset.
4. Optionally run the evaluation section to score the model on the test set with `util.evaluate` (ensure `util.py` from week7 is on the path or copy it into this folder).
