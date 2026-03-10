# Mini RAG: Ask Questions About AI Articles

A simple RAG system over markdown articles about AI. No LangChain—plain ChromaDB, sentence-transformers, and optional OpenAI for answers.

## Data (download required)

The data is **not in this repo**. You must download it from Google Drive before running the notebook.

- **See [DATA.md](DATA.md)** for step-by-step download instructions and where to place the files.

## Contents

- **knowledge_base/** — Markdown documents about AI (what is AI, LLMs, RAG, transformers, embeddings). *Download via [DATA.md](DATA.md).*
- **mini_rag_ai_articles.ipynb** — Notebook that:
  1. Loads and chunks the documents
  2. Creates embeddings (HuggingFace `all-MiniLM-L6-v2`)
  3. Stores vectors in ChromaDB
  4. Visualizes embeddings with t-SNE (2D plot)
  5. Lets you ask questions (retrieval + optional LLM answer)

## Setup

From the `tope-ai-labs` folder:

```bash
pip install chromadb sentence-transformers scikit-learn plotly python-dotenv openai
```

- **Required:** `chromadb`, `sentence-transformers`, `scikit-learn`, `plotly`, `python-dotenv`
- **Optional:** `openai` — for generated answers; without it, the notebook only shows retrieved chunks.

If using OpenAI, set `OPENAI_API_KEY` in your environment or `.env`.

## Run

1. **Download the data** (see [DATA.md](DATA.md)) and place `knowledge_base/` in this folder.
2. Open `mini_rag_ai_articles.ipynb`.
3. Run all cells in order.
4. Use the `ask("your question?")` cell to query; try questions like “What is RAG?” or “How do transformers use attention?”
