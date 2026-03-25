# Beat the Numbers

Improved RAG for the Insurellm evaluation challenge.

## Improvements Over Baseline

| Technique | Baseline | Improved |
|-----------|----------|----------|
| **Query rewriting** | No | Yes — LLM refines user question into focused search query |
| **Retrieval** | Fetch top 10 | Over-fetch 20, LLM rerank, use top 10 |
| **Answer prompt** | Generic | Strict accuracy/completeness/relevance for eval |

## Prerequisites

1. **Vector DB**: Run Week 5 Day 2 to create `week5/vector_db`:
   ```bash
   cd week5 && jupyter notebook
   # Run day2.ipynb cells to build vector_db
   ```

2. **OpenAI API key**: Add `OPENAI_API_KEY=sk-...` to `.env` in repo root or week5.

## Run Evaluation

Compare baseline vs improved RAG on all 150 test questions:

```bash
cd week5 && uv run python community-contributions/adams-bolaji/run_eval.py
```

Or from repo root:

```bash
cd llm_engineering
PYTHONPATH=week5 uv run python week5/community-contributions/adams-bolaji/run_eval.py
```

Output shows MRR, nDCG, keyword coverage, and answer scores (accuracy, completeness, relevance) for both systems, plus delta.

Use `--improved-only` to skip the baseline run (faster, fewer API calls):
```bash
cd week5 && uv run python community-contributions/adams-bolaji/run_eval.py --improved-only
```

## Chat UI

Try the RAG interactively:

```bash
cd week5 && uv run python community-contributions/adams-bolaji/app.py
```

## Files

| File | Purpose |
|------|---------|
| `answer.py` | Improved RAG: `fetch_context`, `answer_question` (drop-in for `implementation.answer`) |
| `run_eval.py` | Run retrieval + answer eval, compare baseline vs improved |
| `app.py` | Gradio chat interface |
