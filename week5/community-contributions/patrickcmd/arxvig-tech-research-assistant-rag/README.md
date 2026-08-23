# arXiv Research Assistant

A RAG chatbot that ingests arXiv papers and answers questions about them with follow-up support.

## How It Works

1. **Ingest** — Searches arXiv for papers on a topic, converts PDFs to markdown via Mistral OCR, chunks them with an LLM, and stores embeddings in ChromaDB.
2. **Answer** — Retrieves relevant chunks using query rewriting + re-ranking, then generates grounded answers citing paper titles.
3. **Chat UI** — Gradio chatbot interface with conversation history.

## Setup

```bash
pip install openai litellm mistralai chromadb gradio arxiv python-dotenv pydantic tqdm tenacity
```

Create a `.env` file:

```
OPENAI_API_KEY=sk-...
MISTRAL_API_KEY=...
```

## Run

**Step 1 — Ingest papers:**

```bash
python ingest.py "transformer neural networks" 5
```

Arguments: `topic` (default: "transformer neural networks"), `k` number of papers (default: 5).

**Step 2 — Launch chatbot:**

```bash
python app.py
```

Opens at `http://localhost:7860`.

## Project Structure

```
ingest.py   — arXiv search, Mistral OCR, LLM chunking, ChromaDB storage
answer.py   — query rewriting, retrieval, re-ranking, RAG answering
app.py      — Gradio chat interface
```