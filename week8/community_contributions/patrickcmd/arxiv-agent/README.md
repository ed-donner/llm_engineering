# arXiv Research Agent

An **agentic RAG** chatbot that can search, ingest, and reason over arXiv papers using a plain tool-calling loop — no frameworks required.

## How It Works

Instead of a fixed retrieve-then-answer pipeline, an LLM agent decides **which tools to call and when**, looping until it has enough context to answer.

### Agent Tools

| Tool | Description |
|------|-------------|
| `search_knowledge_base` | Vector search over pre-ingested paper chunks in ChromaDB |
| `search_arxiv` | Live search the arXiv API for new papers |
| `ingest_papers` | OCR + chunk + embed papers into ChromaDB on demand |
| `get_paper_details` | Fetch full metadata for a specific paper |

### Example Flows

- **Simple Q&A** — agent calls `search_knowledge_base`, answers from results
- **New topic** — `search_arxiv` → `ingest_papers` → `search_knowledge_base` → answer
- **Complex question** — multiple `search_knowledge_base` calls with sub-queries → synthesise
- **Paper comparison** — targeted searches per paper → comparative answer

## Architecture

```
app.py      — Gradio chat UI with agent activity sidebar
agent.py    — Tool-calling loop, system prompt, tool dispatch
tools.py    — Tool implementations (KB search, arXiv search, ingestion, metadata)
answer.py   — Legacy RAG utilities (embeddings, reranking)
ingest.py   — Bulk ingestion CLI (arXiv fetch → Mistral OCR → LLM chunking → ChromaDB)
```

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

**Step 1 — (Optional) Bulk-ingest papers on a topic:**

```bash
python ingest.py "transformer neural networks" 5
```

This pre-populates the knowledge base. The agent can also ingest papers on-the-fly during conversation.

**Step 2 — Launch the agent:**

```bash
python app.py
```

Opens at `http://localhost:7860`.
