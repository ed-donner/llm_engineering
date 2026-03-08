# Week 5 — Samsung Galaxy RAG (SamuelAdebodun)

RAG assistant over Samsung Galaxy mobile devices. Ask about S24, Z Fold/Flip, A series, and software features.

**Models:** OpenAI (gpt-4o-mini), Anthropic (claude-3-5-sonnet), or Ollama (llama3.2 local). Embeddings use OpenAI.

## Setup

1. From this folder (`week5/community-contributions/SamuelAdebodun`), install:
   ```bash
   pip install openai anthropic chromadb gradio python-dotenv
   ```
2. Set in `.env`: `OPENAI_API_KEY` (required for embeddings and OpenAI chat), `ANTHROPIC_API_KEY` (optional, for Claude). For Ollama, run `ollama run llama3.2` locally.
3. Open `week5_rag_galaxy.ipynb` and run all cells. The Gradio chat launches at the end; pick a model in the dropdown.

## Knowledge base

- `knowledge_base/galaxy_s24.md` — S24, S24+, S24 Ultra
- `knowledge_base/galaxy_z_fold_flip.md` — Z Fold 6, Z Flip 6
- `knowledge_base/galaxy_a_series.md` — A55, A35, A15/A25
- `knowledge_base/galaxy_features_software.md` — One UI, Galaxy AI, Knox, DeX, updates

You can add more `.md` files under `knowledge_base/` and re-run the load + chunk + Chroma cells to re-index.
