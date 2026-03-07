# CV Review RAG

Simple RAG over resumes using: LLM chunking → Chroma + embeddings → retrieve → rerank → answer.

## Setup

From repo root (or ensure `openai`, `chromadb`, `litellm`, `pydantic`, `python-dotenv`, `tenacity`, `tqdm` are installed). Set `OPENAI_API_KEY` in `.env` or environment.

## Usage

1. **Ingest resumes once** (reads `resume/*.txt`, chunks with LLM, embeds, writes `cv_db/`):

   ```bash
   uv run ingest.py
   ```

2. **Start the Gradio chatbot** (opens in browser):

   ```bash
   uv run main.py
   ```

   Example questions: *"Who has Python experience?"*, *"Compare backend skills of the candidates."*
