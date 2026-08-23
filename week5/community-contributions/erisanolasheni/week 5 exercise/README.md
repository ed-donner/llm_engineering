# Week 5 Exercise – Beat the Numbers (Improved RAG)

Challenge: improve retrieval and answer metrics on the Insurellm RAG evaluation (query expansion, reranking, prompts).

## What’s in this folder

- **`improved_rag.py`** – Drop-in replacement for `implementation.answer`:
  - **Query rewriting**: LLM rewrites the user question into a short, entity-rich search query before retrieval.
  - **Larger retrieval + rerank**: Fetch top 20 by similarity, then LLM reranks by relevance to the original question; return top 10.
  - **Stricter answer prompt**: Emphasises accuracy (exact numbers/facts), completeness, and relevance so the model stays on-topic and complete.

- **`run_eval.py`** – Runs the official evaluation (retrieval MRR/nDCG/coverage and answer accuracy/completeness/relevance) using the improved pipeline by patching `evaluation.eval`.

## API keys and base URLs

Set them in a **`.env`** file (repo root or week5 directory). The script loads them via `load_dotenv(override=True)`.

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Used by LangChain (answer + embeddings) and LiteLLM (query rewrite, rerank). Required for default OpenAI. |
| `OPENAI_API_BASE` | Optional. Override API base URL (e.g. OpenRouter: `https://openrouter.ai/api/v1`). If set, both LangChain and LiteLLM use it when using the default provider. |
| `RAG_MODEL` | Optional. LLM for answers, rewrite, and rerank (default: `gpt-4.1-nano`). |
| `RAG_EMBEDDING_MODEL` | Optional. Embedding model (default: `text-embedding-3-large`). |

Example `.env`:

```bash
OPENAI_API_KEY=sk-...
# Optional: use OpenRouter or another proxy
# OPENAI_API_BASE=https://openrouter.ai/api/v1
```

## How to run

1. From the **week5** directory (so `evaluation` and `implementation` resolve):

   ```bash
   cd week5
   uv run python "community-contributions/erisanolasheni/week 5 exercise/run_eval.py"
   ```

2. Or from repo root with `week5` on `PYTHONPATH`:

   ```bash
   cd llm_engineering
   PYTHONPATH=week5 uv run python "week5/community-contributions/erisanolasheni/week 5 exercise/run_eval.py"
   ```

3. Ensure `vector_db` and `knowledge-base` exist under `week5` (run the week 5 ingest/notebooks first if needed).

## Comparison with baseline

- **Baseline**: `implementation.answer` – direct retriever (k=10), no query rewrite, no rerank, simple context prompt.
- **This exercise**: Query rewrite → retrieve 20 → rerank → top 10 → answer with a prompt that stresses accuracy, completeness, and relevance.

Compare by running the standard evaluator (baseline) then `run_eval.py` (improved) and checking MRR, nDCG, coverage, and the three answer scores.
