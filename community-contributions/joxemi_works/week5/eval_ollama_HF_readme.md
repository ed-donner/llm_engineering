# Eval README (`*4.py` Pipeline)

## What Changed vs `*3.py`
`*4.py` keeps the same local stack (Ollama + HuggingFace embeddings + Chroma), but adds an iterative tuner:

- `evaluation/tuner_ollama_HF.py` to auto-search `RETRIEVAL_K` and `FINAL_K`.
- Stratified test sampling by category (not just first rows).
- Multi-fold scoring to reduce one-shot variance.
- Combined objective (`score`) and derived `loss = 1 - score`.
- Compact runtime traces per candidate, fold, and test.

## Current Tuner Setup
- `RETRIEVAL_GRID = [10, 12, 14]`
- `FINAL_GRID = [5, 6]`
- `N_FOLDS = 2`
- `PER_CATEGORY = 5`
- `MAX_TESTS = None` (fold size is driven by `PER_CATEGORY`)
- `RANDOM_SEED = 42`

With 7 categories, each fold targets ~35 tests (5 per category), if available.

## How Tuner Selects Tests
1. Load all tests from `evaluation/tests.jsonl`.
2. Group tests by `category`.
3. For each category, shuffle with deterministic seed.
4. Pick up to `PER_CATEGORY` tests per category.
5. If a category has fewer tests, fill from remaining pool.
6. Build fold 1 with seed `42`, fold 2 with seed `43`.

This gives reproducible, category-balanced subsets.

## Objective Function (`score` / `loss`)
`tuner_ollama_HF.py` combines retrieval + answer metrics:

- Retrieval: `mrr`, `ndcg`, `coverage`
- Answer: `accuracy`, `completeness`, `relevance`

Current weights:
- `mrr`: 0.20
- `ndcg`: 0.15
- `coverage`: 0.10
- `accuracy`: 0.25
- `completeness`: 0.15
- `relevance`: 0.15

`loss = 1 - score`

## Files and Responsibilities
### `pro_implementation/answer_ollama_HF.py`
- Same local RAG logic as `answer_ollama_HF.py`.
- Exposes runtime knobs:
  - `set_retrieval_config(retrieval_k, final_k)`
  - `get_retrieval_config()`

### `evaluation/eval_ollama_HF.py`
- Evaluation logic for the `answer_ollama_HF.py` and `test_ollama_HF.py` pipeline.

### `evaluation/test_ollama_HF.py`
- Test schema + loader for `tests.jsonl`.

### `evaluation/tuner_ollama_HF.py`
- Grid-search over `RETRIEVAL_K`/`FINAL_K`.
- Evaluates each candidate across folds.
- Logs results to:
  - `evaluation/results4/tuning_results.jsonl`

### `app_ollama_HF.py`
- Gradio chat UI using `answer_ollama_HF.py`.

### `evaluator_ollama_HF.py`
- Gradio evaluation dashboard using `eval_ollama_HF.py`.

## Execution (from script folder style)
You can run directly from `evaluation/`:

```powershell
cd .\week5\evaluation
uv run eval_ollama_HF.py 0
uv run tuner_ollama_HF.py
```

Dashboard from `week5/`:

```powershell
cd ..\
uv run python evaluator_ollama_HF.py
```

## Recommended Workflow
1. Run `tuner_ollama_HF.py` and keep top candidate.
2. Validate with `evaluator_ollama_HF.py` (full dashboard run).
3. If better than baseline, fix those Ks in `answer_ollama_HF.py`.
4. Keep `tuning_results.jsonl` as experiment history.
