# Week 5 Exercise: Company Website RAG Assistant (cwait)

Personal knowledge worker for the **Week 5 RAG** exercise. This solution powers a **company-website Q&A** using only the existing company knowledge base (about, overview, culture, careers).

## What it does

- **Assembles** all company docs from `week5/knowledge-base/company/` (about.md, overview.md, culture.md, careers.md)
- **Vectorises** them in **ChromaDB** (HuggingFace `all-MiniLM-L6-v2` embeddings, chunk size 1000, overlap 200)
- **RAG chat**: retrieves relevant chunks and generates answers via an LLM (gpt-4.1-nano) for public questions about the company

## Run

Open the notebook and run all cells:

```bash
jupyter notebook week5/community-contributions/cwait/week5_igniters_cwait.ipynb
# or
jupyter lab week5/community-contributions/cwait/week5_igniters_cwait.ipynb
```

Run from the repo root so the notebook finds `knowledge-base/company`. The last cell launches the Gradio chat UI.

**Requires**

- `.env` with `OPENAI_API_KEY` (for the chat model)
- Dependencies from the main project (`uv sync` or `pip install -e .` from repo root)

## Rebuild the vector DB

To re-ingest and rebuild Chroma from the company docs, set `REBUILD_DB = True` in the **Config** cell of the notebook, then re-run the cells that load documents, chunk, and build the vector store.

## Files

| File | Purpose |
|------|--------|
| `week5_igniters_cwait.ipynb` | Ingest, Chroma, RAG + Gradio chat (run all cells, launch UI in last cell) |
| `company_chroma_db/` | Created on first run; persisted Chroma vector store |

## Tech

- **LangChain**: `DirectoryLoader`, `RecursiveCharacterTextSplitter`, `Chroma`, `ChatOpenAI`
- **Embeddings**: HuggingFace `all-MiniLM-L6-v2` (no extra API key)
- **LLM**: OpenAI `gpt-4.1-nano` (set in notebook config; override via env if needed)
- **UI**: Gradio `ChatInterface`
