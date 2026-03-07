# Week 7 Community Contribution – Plan (abdussamadbello)

This document plans your Week 7 contribution so it matches the quality and structure of your Week 6 contribution (fine-tuning + baseline comparison + category-stratified eval + notes).

---

## Goal

Implement the **“Price is Right” open-source fine-tuning pipeline**: prepare prompt data (Day 2), point to or document training (Days 3–4 in Colab), and **evaluate** your fine-tuned Llama model with the same kind of analysis you did in Week 6 (baseline comparison, category breakdown, short notes).

---

## Folder and naming

- **Path**: `week7/community_contributions/abdussamadbello/`
- **Naming**: Week 7 uses `community_contributions` (underscore), not `community-contributions`.

---

## Deliverables (checklist)

### 1. README.md

- **Title**: e.g. “Week 7 – Open-Source Pricer Fine-Tuning (QLoRA) (abdussamadbello)”.
- **What’s included**: List each notebook and what it does (Day 2 prep, Eval, optional training notes).
- **Setup**: Run from repo root; `pip install` for week7 (e.g. `transformers`, `peft`, `bitsandbytes`, `huggingface_hub`, `python-dotenv`); `.env` with `HF_TOKEN`; note if Colab is needed for training/eval with GPU.
- **How to run**: Step-by-step for Day 2 notebook and Eval notebook (and Colab link for training if you use it).
- **Notes**: Any gotchas (e.g. 4-bit load, VRAM, using same tokenizer as Day 2).

### 2. Day 2 – Prompt data and base model (in repo)

- **Notebook**: `week7-day2-prompt-data.ipynb` (or similar).
- **Content**:
  - Load items from Hub (`ed-donner/items_lite` or `items_full`), same as `week7/day2.ipynb`.
  - Use `pricer.items.Item`, `BASE_MODEL = "meta-llama/Llama-3.2-3B"`, `AutoTokenizer.from_pretrained(BASE_MODEL)`.
  - Token-count histogram, choose `CUTOFF` (e.g. 110), report truncation stats.
  - Call `item.make_prompts(tokenizer, CUTOFF, do_round=True)` for train/val, `do_round=False` for test.
  - Optional: push to your own Hub dataset (e.g. `abdussamadbello/items_prompts_lite`) via `Item.push_prompts_to_hub(...)` so you own the exact data you train on.
  - Short markdown: what the prompt/completion format is and why (same as in week7-notes).
- **Run from**: Repo root (so `pricer` is importable). No GPU required for this notebook.

### 3. Training (Colab or doc only)

- **Option A (recommended for first version)**: Don’t implement training in the repo. In the README and/or notebook:
  - Link to the official Week 7 Colab notebooks for Day 1 (QLoRA), Day 3 (Train Part 1), Day 4 (Train Part 2).
  - Say: “Use the prompt dataset produced by `week7-day2-prompt-data.ipynb` (or `ed-donner/items_prompts_lite`) in that Colab; after training, download or push your adapter to the Hub for the Eval notebook.”
- **Option B**: Add a short `TRAINING.md` or section in README with:
  - Colab link(s).
  - Key config (base model, LoRA rank, batch size, steps) and where you save the adapter (e.g. `abdussamadbello/pricer-qlora-lite`).

### 4. Day 5 – Eval notebook (main contribution)

- **Notebook**: `week7-eval.ipynb` (or `week7-assignment.ipynb`).
- **Assumption**: You have a fine-tuned adapter (from Colab or Hub). The notebook can assume the adapter is on the Hub (e.g. `abdussamadbello/pricer-qlora-lite`) or loaded from a local path.
- **Content**:
  1. **Setup**: Same as Week 6 style – run from repo root or Colab; env for `HF_TOKEN`; installs for `transformers`, `peft`, `bitsandbytes`, `accelerate`, etc.
  2. **Load data**: Load test items (either `Item.from_hub` and use `pricer.evaluator`, or load prompt/completion test set and use a small wrapper that exposes `price` or `completion` for the evaluator).
  3. **Load model**: Base `Llama-3.2-3B` in 4-bit + your PEFT adapter; same tokenizer as Day 2.
  4. **Predictor**: A `pricer_fn(item)` that:
     - Builds the test prompt (question + summary + “Price is $”).
     - Generates completion; parses number with regex or `Tester.post_process`.
     - Returns predicted price.
  5. **Evaluate**: Call `evaluate(pricer_fn, test_items, size=200)` from `pricer.evaluator` (or equivalent if you use prompt/completion dicts and a thin wrapper).
  6. **Baseline comparison**: Run the **base model** (no adapter) on the same test subset; report mean absolute error (and optionally RMSE/R²) for base vs fine-tuned in a small table or markdown.
  7. **Category-stratified eval**: Group test items by `item.category`; compute MAE per category for fine-tuned (and optionally for base); show a table and bar chart (e.g. pandas + matplotlib or plotly), same idea as Week 6.
  8. **Notes**: 2–3 sentences on why some categories do better/worse (scale, sample size, wording).
  9. **Optional “reasons”**: One cell that, for a few examples, asks the model: “Why might this product cost around $X?” (you can use the same model or a separate API model) and shows one-sentence reasons.

### 5. Optional extras

- **Results table**: Add your run to a small “My results” table in the README (e.g. base Llama MAE, fine-tuned MAE, fine-tuned MAE by category).
- **Colab badge**: If the Eval notebook is also provided as a Colab notebook, add an “Open in Colab” badge/link in the README.

---

## Suggested order of work

1. Create folder and **README.md** (skeleton with “What’s included”, “Setup”, “How to run”, “Notes”).
2. Implement **week7-day2-prompt-data.ipynb** (follow `week7/day2.ipynb` and `pricer.items`).
3. Run training once in Colab (using official Week 7 Colab or your own) and save adapter to Hub (or keep a local path for dev).
4. Implement **week7-eval.ipynb** (load adapter, predictor, `evaluate`, baseline comparison, category stratification, notes).
5. Update README with real numbers, Colab links, and any gotchas.
6. Optionally add TRAINING.md or “reasons” cell.

---

## Dependencies (for README)

Suggested for Day 2 (repo):

```bash
pip install python-dotenv huggingface_hub datasets transformers
```

Suggested for Eval (repo or Colab, GPU):

```bash
pip install torch transformers peft bitsandbytes accelerate python-dotenv huggingface_hub
# and pricer from repo if running locally
```

---

## Parity with Week 6 contribution

| Week 6 (your contribution)     | Week 7 (this plan)                    |
|----------------------------------|---------------------------------------|
| Fine-tune GPT-4.1-nano (API)     | Fine-tune Llama with QLoRA (Colab)    |
| JSONL upload, job, poll          | Day 2 prompt data; training in Colab |
| evaluate() on test set          | Same evaluate() on test set          |
| Baseline: base vs fine-tuned    | Baseline: base Llama vs fine-tuned    |
| Category-stratified MAE + chart | Category-stratified MAE + chart       |
| Notes on categories             | Notes on categories                   |
| Optional “reasons” cell         | Optional “reasons” cell               |

Use this plan as a checklist; tick off each section as you implement it.
