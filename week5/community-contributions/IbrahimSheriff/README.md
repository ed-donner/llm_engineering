# Galdunx RAG Chatbot & Evaluation

A RAG (Retrieval-Augmented Generation) chatbot and evaluation suite for the **Galdunx** knowledge base. Chat over Galdunx docs via a Gradio UI and run retrieval (MRR) and answer-quality (LLM-as-judge) evals.

## Overview

- **Chat UI** — Ask questions about Galdunx; answers use requery + rerank over a ChromaDB vector store.
- **Evaluation** — Gradio app to run MRR (retrieval) and LLM-as-judge (answer quality) on a configurable eval set.

## Prerequisites

- Python 3.10+
- Dependencies from the repo (e.g. `langchain-*`, `chromadb`, `gradio`, `python-dotenv`).

### Environment

Create a `.env` in this directory (or repo root) if using API-backed embeddings/LLM:

- **`OPENROUTER_API_KEY`** — If set, uses OpenRouter for embeddings (`openai/text-embedding-3-small`) and chat (`openai/gpt-4o-mini`). Otherwise uses local HuggingFace embeddings and OpenAI `gpt-4o-mini` for chat (OpenAI key required for that).

## Quick Start

Run all commands from `week5/IbrahimSheriff` (or ensure this directory is on `PYTHONPATH`).

### 1. Ingest the knowledge base

Builds the vector store from `knowledge-base/*.md`:

```bash
python ingest.py
```

If the Gradio chat app is running, stop it first or ingestion may fail (DB locked).

### 2. Chat app

```bash
python app.py
```

Opens a Gradio chat interface. Use **Re-ingest knowledge base** to refresh the vector store from the UI.

### 3. Evaluation app

```bash
python eval_app.py
```

- **Eval set:** Use the default Galdunx eval set or paste custom JSON.
- **Run evaluation:** Runs MRR (retrieval), then RAG answers + LLM-as-judge; shows summary and per-example details.

Custom eval JSON format:

```json
[
  {
    "question": "Your question?",
    "expected_sources": ["filename.md"],
    "expected_answer": "Optional expected answer for judge."
  }
]
```

Default eval set is loaded from `eval_data.json` when present.

## Project structure

| File / folder        | Purpose |
|----------------------|--------|
| `app.py`             | Gradio chat UI; calls `answer_question` and optional re-ingest. |
| `answer.py`          | RAG pipeline: requery, retrieve, merge, rerank, then LLM answer. |
| `ingest.py`          | Loads `knowledge-base/*.md`, chunks, embeds, writes to `vector_db/`. |
| `eval_app.py`        | Gradio UI for running MRR + LLM-as-judge evaluation. |
| `evaluation.py`      | Eval logic: MRR, default eval set, LLM judge; used by `eval_app.py`. |
| `eval_data.json`     | Default eval set (questions + expected sources/answers). |
| `knowledge-base/`    | Source Markdown files (e.g. about Galdunx, web dev, UI/UX, 10K Store). |
| `vector_db/`         | ChromaDB persistence (created by `ingest.py`). |

## RAG pipeline (answer.py)

1. **Requery** — LLM generates an extra retrieval-oriented query from the user question and history.
2. **Retrieve** — Vector search for both the combined user input and the AI query; results merged and deduped.
3. **Rerank** — Top chunks reordered by relevance with an LLM (structured output).
4. **Answer** — Top reranked chunks are used as context for the final answer.

## Notes

- Embeddings and DB path are shared between `ingest.py` and `answer.py` so the chat app uses the same vector store.
- If you see “vector database is locked”, stop the Gradio chat app before re-running ingest.
- For local embeddings, NumPy 2.x can conflict with some setups; the ingest script suggests using `OPENROUTER_API_KEY` or `uv pip install 'numpy<2'` if needed.
