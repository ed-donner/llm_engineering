# Week 7 – Open-Source Pricer: Multi-Task, RAG, and Reasons (abdussamadbello)

This contribution extends the **“Price is Right”** capstone with the **same Week 7 model** (QLoRA Llama):

1. **Multi-task**: Predict **category + price** in one completion (`Category: X. Price is $Y.00`).
2. **RAG**: Retrieve similar products and add them to the prompt; **compare** pricer-only vs pricer+RAG (MAE).
3. **Reasons**: One-sentence explanation (“Why might this product cost around $X?”).

## What’s included

- **`multitask_data.py`** – Multi-task prompt/completion format and parsing:
  - `build_multitask_prompt(summary)`, `build_multitask_completion(category, price)`, `parse_multitask_completion(text)` → (category, price).
  - `item_to_multitask_datapoint(item, tokenizer, max_tokens, do_round)` for dataset build.

- **`rag_retriever.py`** – RAG over similar products:
  - `RAGIndex(items)`: embed summaries (sentence-transformers), retrieve top-k.
  - `format_similar_products(query, k)` for prompt context.
  - Requires `sentence-transformers`.

- **`reasons.py`** – One-sentence reasons:
  - `get_reason(..., generate_fn=...)` (same model, second prompt) or `get_reason(..., use_api=True)` (e.g. GPT-4o-mini).

- **`week7-multitask-prompt-data.ipynb`** – Build multi-task dataset:
  - Load items from Hub, tokenizer, CUTOFF; build prompt/completion for train/val/test.
  - Optional push to Hub (e.g. `abdussamadbello/items_prompts_multitask_lite`).

- **`week7-eval-multitask-rag-reasons.ipynb`** – Eval notebook:
  - Load base + PEFT adapter; multi-task predictor (category + price).
  - Build RAG index from train; **pricer_only** vs **pricer_with_rag**; run `evaluate()` for both and compare MAE.
  - **Reasons**: sample of items with one-sentence reason (same model or API).

- **`CONTRIBUTION_PLAN.md`** – Original plan and checklist.

## Setup

Run from the **repository root**:

```bash
cd /path/to/llm_engineering
pip install python-dotenv huggingface_hub datasets transformers
# For eval (GPU): pip install torch peft bitsandbytes accelerate sentence-transformers
# For reasons via API: pip install litellm
```

Create a `.env` in the repo root (do not commit it):

```bash
HF_TOKEN=hf_...
# Optional for reasons: OPENAI_API_KEY=sk-...
```

## How to run

1. **Multi-task prompt data**: Open `week7-multitask-prompt-data.ipynb` from repo root; run all cells. No GPU. Set `MULTITASK_DATASET` to push to Hub.
2. **Training**: Use Week 7 Colab (Days 3–4) with the **multi-task** dataset (same base model; only dataset format changes). Save adapter to Hub.
3. **Eval**: Open `week7-eval-multitask-rag-reasons.ipynb`, set `ADAPTER_PATH` to your adapter (Hub ID or path). Run; compare pricer-only vs pricer+RAG; view reasons sample. GPU or Colab.

## Checklist (for PR)

- [x] Changes are under `week7/community_contributions/abdussamadbello/`.
- [x] No edits to repo files outside this folder.
- [x] README describes setup and how to run.

## Notes

- **Multi-task format**: Completion is `Category: <cat>. Price is $<num>.00`; parser extracts both for eval.
- **RAG**: Index is built from train items (embedding model: `all-MiniLM-L6-v2`). Top-k=5 by default; configurable in the notebook.
- **Reasons**: Use same model (second prompt) or API (`use_api=True` with `OPENAI_API_KEY`) for one-sentence explanations.
- Evaluation uses `pricer.evaluator.evaluate()` from `week7/pricer/`.
