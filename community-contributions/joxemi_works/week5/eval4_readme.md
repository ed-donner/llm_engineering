# Eval README (`*4.py` Pipeline)

## What Changed vs `*3.py`
`*4.py` keeps the same local stack (Ollama + HuggingFace embeddings + Chroma), but adds an iterative tuner:

- `evaluation/tuner4.py` to auto-search `RETRIEVAL_K` and `FINAL_K`.
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
`tuner4.py` combines retrieval + answer metrics:

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
### `pro_implementation/answer4.py`
- Same local RAG logic as `answer3.py`.
- Exposes runtime knobs:
  - `set_retrieval_config(retrieval_k, final_k)`
  - `get_retrieval_config()`

### `evaluation/eval4.py`
- Same evaluation logic as `eval3.py`, now targeting `answer4.py` and `test4.py`.

### `evaluation/test4.py`
- Test schema + loader for `tests.jsonl`.

### `evaluation/tuner4.py`
- Grid-search over `RETRIEVAL_K`/`FINAL_K`.
- Evaluates each candidate across folds.
- Logs results to:
  - `evaluation/results4/tuning_results.jsonl`

### `app4.py`
- Gradio chat UI using `answer4.py`.

### `evaluator4.py`
- Gradio evaluation dashboard using `eval4.py`.

## Execution (from script folder style)
You can run directly from `evaluation/`:

```powershell
cd .\week5\evaluation
uv run eval4.py 0
uv run tuner4.py
```

Dashboard from `week5/`:

```powershell
cd ..\
uv run python evaluator4.py
```

## Recommended Workflow
1. Run `tuner4.py` and keep top candidate.
2. Validate with `evaluator4.py` (full dashboard run).
3. If better than baseline, fix those Ks in `answer4.py`.
4. Keep `tuning_results.jsonl` as experiment history.
