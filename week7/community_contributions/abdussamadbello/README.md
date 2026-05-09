# Week 7 – Multi-task + RAG (abdussamadbello)

**Two ideas in one file:**

1. **Multi-task**: Predict **category + price** in one completion (`Category: X. Price is $Y.00`). Build dataset and use for training/eval.
2. **RAG**: Compare **pricer only** vs **pricer + RAG** (similar products in prompt); report MAE for both.

All code is in **one notebook**: `week7-multitask-rag.ipynb`.

## What’s in this submission

- **week7-multitask-rag.ipynb** – Single notebook: path setup, helpers (multi-task + RAG) inline, load data, build multi-task dataset, load model, pricer_only vs pricer_with_rag, run `evaluate()` for both.
- **README.md** – This file.

## Setup

From repo root:

```bash
pip install python-dotenv huggingface_hub datasets transformers sentence-transformers
# For eval (GPU): pip install torch peft bitsandbytes accelerate
```

Use `.env` at repo root (do not commit): `HF_TOKEN=...`. Never hardcode API keys.

## How to run

1. Run from repo root. Open `week7/community_contributions/abdussamadbello/week7-multitask-rag.ipynb`.
2. Run all cells. Multi-task dataset is built; set `MULTITASK_DATASET` to push to Hub. Use Week 7 Colab for training with that dataset.
3. Set `ADAPTER_PATH` to your adapter (Hub ID or path), then run the last cells to compare pricer only vs pricer + RAG.

## PR submission

- Only files under `week7/community_contributions/abdussamadbello/`.
- No config files. Stage only: `git add week7/community_contributions/abdussamadbello/`
- Clear notebook outputs before submit (`nbstripout week7-multitask-rag.ipynb` or Edit → Clear all outputs).

