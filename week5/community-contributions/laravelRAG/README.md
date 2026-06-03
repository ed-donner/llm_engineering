# Laravel Docs RAG (Week 5 aligned)

RAG over Laravel documentation using **LangChain** loaders and **RecursiveCharacterTextSplitter**, **Chroma**, **OpenAI** embeddings, and **Ollama** for chat. Optional **query rewrite** and **rerank** and a **Gradio** UI.

## Main entry: notebook

Open and run **`Laravel_RAG.ipynb`** from the `laravelRAG` directory. It runs:

1. **Ingest** — load docs, split, embed, save to Chroma  
2. **Chat** — Gradio interface (inline in the notebook)

Run the notebook from the `laravelRAG` folder (e.g. in VS Code/Cursor: open the folder, then open the notebook).

## Setup

- Install repo dependencies (from repo root): `uv sync` or `pip install -e .`
- Put Laravel docs in `laravel-docs/` (markdown files under any subdirs).
- Set `OPENAI_API_KEY` (e.g. in a `.env` file in this folder or repo root) for embeddings.
