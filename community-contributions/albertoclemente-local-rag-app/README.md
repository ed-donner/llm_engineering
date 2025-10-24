# Local RAG WebApp

A completely local Retrieval-Augmented Generation (RAG) web app for document Q&A, **specialized for AI/ML documentation and research**. Upload AI-related documents, research papers, tutorials, and more — ask questions and get accurate, properly formatted answers — no cloud required.

## ✨ Features

- **100% local**: data never leaves your machine
- **🤖 AI/ML specialization**: optimized for AI and machine learning content with 13 specialized categories (LLMs, Computer Vision, MLOps, AI Research, AI Agents & MCP, etc.)
- **Multi-format document support**: PDF, DOCX, PPTX, HTML, Images (with OCR*) — auto-converted to Markdown via Docling
- **AI-powered categorization**: automatic document categorization with confidence scores and subcategories
- **Category filtering**: browse and filter documents by categories in the UI
- **Smart RAG**: adaptive chunking + dynamic-k retrieval
- **Conversation memory**: LLM remembers last 5 turns (10 messages) for follow-up questions
- **Conversation history**: SQLite-based persistence with auto-generated AI titles
- **Streaming replies**: live token streaming over WebSocket
- **Sources panel**: see which documents informed each answer with clickable citations
- **Performance profiles**: Eco / Balanced / Performance
- **Modern UI**: Next.js 15 with dark/light theme support
- **Message persistence**: Keeps your prompts visible even when switching conversations during generation

_*OCR requires HuggingFace token - set `HF_TOKEN` environment variable to enable image processing_

## Simple Start (No Git Needed — for non‑experts)

No Git required: download the ZIP and run the one‑command script.
This is the easiest path for non‑experts on macOS.

For developers comfortable with Git and the command line. Please note that this section assumes familiarity with Git commands and the terminal.
- Docker Desktop: https://www.docker.com/products/docker-desktop/
- Ollama (Local LLM): https://ollama.ai/
- Node.js 18+ (LTS): https://nodejs.org/ or `brew install node`
- Python 3.9+ (macOS usually has `python3` preinstalled)

2) Download the app (ZIP)
- Open the project page in your browser: https://github.com/albertoclemente/local-rag-app
- Click the green “Code” button → “Download ZIP”
- Unzip it (double‑click). You’ll get a folder like `local-rag-app-main`.

3) Start everything automatically (one command)
- Open Terminal and run these commands (adjust the path as needed):

```bash
cd ~/Downloads/local-rag-app-main
chmod +x scripts/quick_try.sh
./scripts/quick_try.sh
```

- When it finishes starting, open the UI: http://localhost:3000

4) If the one‑command script doesn’t work, do it manually
- Start Qdrant (vector DB):
```bash
docker compose -f docker/docker-compose.yml up -d qdrant
```
- Start Ollama and pull a model:
```bash
ollama serve &
ollama pull qwen2.5:7b-instruct
```
- Start the backend (FastAPI):
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Start the frontend (Next.js):
```bash
cd frontend
npm install
npm run dev
```
- Open the app: http://localhost:3000

5) Use it
- Click “Upload” to add PDF/DOCX/TXT/MD/EPUB files
- Ask your question in the chat input
- Toggle the sources panel with the “i” icon to see which docs were used

Tips
- First run may take a minute (model pull, first build). Refresh if the UI is blank.
- If ports are busy: stop other apps using 3000/8000/6333 or reboot Docker Desktop.
- To stop everything from the one‑command run, press Ctrl+C in the Terminal windows.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker (for Qdrant)
- Ollama (local LLM): https://ollama.ai/

### 1) Clone

```bash
git clone https://github.com/albertoclemente/local-rag-app.git
cd local-rag-app
```

### 2) Start vector database (Qdrant)

```bash
docker compose -f docker/docker-compose.yml up -d qdrant
```

### 3) Backend

```bash
cd backend
pip install -e .

# Start Ollama and pull a model (choose one)
ollama serve &
ollama pull qwen2.5:7b-instruct   # default here
# or: ollama pull llama3.1:8b

# Start FastAPI (reload for dev)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4) Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5) Open the app

- UI: http://localhost:3000
- API docs: http://localhost:8000/api/docs
- API health: http://localhost:8000/health

If the page doesn't load, give it a few seconds on first run and refresh.

## ⚡ Quick Try (one command)

Runs Qdrant (Docker), Backend (FastAPI), and Frontend (Next.js) for a quick local demo:

```bash
chmod +x scripts/quick_try.sh
./scripts/quick_try.sh
```

Notes:
- Requires Docker, Python, Node, and (ideally) Ollama installed.
- Press Ctrl+C in the terminal to stop both backend and frontend.

## 🐳 Docker (Frontend + Backend + Qdrant)

Run everything in Docker for a one-command start.

```bash
docker compose -f docker/docker-compose.yml --profile full up -d
```

Or use the helper that builds, starts, waits, and opens your browser automatically (macOS):

```bash
chmod +x scripts/docker_up_and_open.sh
./scripts/docker_up_and_open.sh
```

Services
- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/api/docs
- Backend health: http://localhost:8000/health
- Qdrant: http://localhost:6333

Notes
- Ollama runs on your host at `http://localhost:11434`. Make sure it’s serving and a model is pulled:
```bash
ollama serve &
ollama pull qwen2.5:7b-instruct
```
- On macOS/Windows, containers reach your host via `host.docker.internal` (preconfigured). On Linux, you may need to map the host gateway or expose Ollama differently.

Persistence
- Documents, parsed data, indices, and logs persist under `~/RAGApp` by default.
- In Docker, the backend binds `~/RAGApp` into the container (`/app/data`) and Qdrant binds `~/RAGApp/qdrant_data`.
- To change location, set `RAG_DATA_DIR` before `docker compose up`.

Warning
- Running `docker compose down -v` removes named volumes. With the new bind-mounts, data lives in your home folder and is not removed by `-v`. Do not delete `~/RAGApp` if you want to keep documents.

Migration
- If you previously used Docker with named volumes and want to migrate that data:
```bash
./scripts/migrate_docker_volumes.sh
```
- This copies old volume data into `~/RAGApp` so it persists with the new bind-mount setup.

## 🧭 How To Use

### Upload documents
- Click the "Upload" button in the UI to add documents
- **Supported formats**: PDF, DOCX, PPTX, HTML, Images (PNG, JPG, TIFF, BMP), Markdown, AsciiDoc
- Documents are automatically converted to Markdown using Docling for better structure preservation
- **Image OCR**: To enable OCR for images and scanned PDFs, set the `HF_TOKEN` environment variable with your HuggingFace token
- **AI categorization**: Documents are automatically categorized by AI with confidence scores
- The status bar shows indexing progress; the Documents list updates to "indexed"

### Browse and filter documents
- **Category filtering**: Use the category filter in the Documents panel to browse by category
- **Search**: Use the search bar to find documents by name
- **Tag filtering**: Filter documents by tags
- **Category view**: Toggle "Group by Category" to organize documents by their categories
- **Category statistics**: View category distribution and document counts in the UI

### Ask questions
- Type queries in the chat input
- Responses render with **Markdown** and **KaTeX** (math supported: inline `$a^2+b^2=c^2$` or blocks with `$$...$$`)
- The LLM has **conversation memory** — it remembers your last 5 exchanges within the same session
- Ask follow-up questions naturally: "What about X?" or "Can you explain that differently?"

### Manage conversations
- **Conversation history**: All your conversations are saved in the left sidebar
- **Auto-generated titles**: Each conversation gets an AI-generated title based on the first exchange
- **Switch conversations**: Click any conversation to resume it — the LLM remembers the context
- **New chat**: Click the "+ New Chat" button to start a fresh conversation
- **Search**: Use the search bar in the sidebar to find past conversations
- **Delete**: Hover over a conversation and click the trash icon to delete it

### View sources
- Toggle the sources panel with the "i" icon in the header
- See which documents informed each answer with clickable citations
- Citations show the relevant text chunk and similarity score

### Theme
- The UI supports both **light and dark themes**
- All text, including chat messages and markdown content, is readable in both themes

### Model indicator
- The header shows the active LLM model name (default: Qwen 2.5 7B Instruct)

## 🛠️ Configuration

Create `backend/.env` (values shown are sensible defaults):

```bash
# Performance profile
RAG_PROFILE=balanced   # eco|balanced|performance

# Data directory (default expands to ~/RAGApp)
RAG_DATA_DIR=~/RAGApp

# Services
QDRANT_URL=http://localhost:6333
OLLAMA_HOST=http://localhost:11434

# Models
RAG_LLM_MODEL=qwen2.5:7b-instruct  # or llama3.1:8b, etc.
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# OCR for images (optional - requires HuggingFace account)
HF_TOKEN=your_huggingface_token_here

# RAG parameters
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=200
RAG_MAX_CONTEXT_TOKENS=4000

# Debug logging
RAG_DEBUG=false
```

## 🏗️ Architecture

```
┌───────────────────┐   ┌──────────────────┐   ┌─────────────────┐
│     Next.js UI    │◄──│  FastAPI + WS    │◄──│     Qdrant      │
│  (React/TypeScript)│  │   (Backend)      │   │  (Vector Store) │
└───────────────────┘   └──────────────────┘   └─────────────────┘
                     │                      │                       │
                     │                      ▼                       │
                     │             ┌─────────────────┐              │
                     │             │     Ollama      │              │
                     │             │   (Local LLM)   │              │
                     └─────────────┴─────────────────┴──────────────┘
```

### Core Components

- Frontend: Next.js (React + TypeScript)
- Backend: FastAPI + WebSocket streaming
- Vector store: Qdrant (local)
- LLM: Ollama (qwen2.5, llama3.x, etc.)
- Embeddings: Sentence Transformers (local)

## 📁 Project Structure

```
RAG_APP/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── api_complete.py         # REST endpoints (/api/status, /api/query, etc.)
│   │   ├── ws.py                   # WebSocket streaming
│   │   ├── models.py               # Pydantic models
│   │   ├── settings.py             # Configuration
│   │   ├── storage.py              # File operations (uploads, parsed)
│   │   ├── chunking.py             # Adaptive chunking
│   │   ├── embeddings.py           # Local embeddings
│   │   ├── qdrant_index.py         # Vector store operations
│   │   ├── retrieval.py            # Retrieval logic
│   │   ├── llm.py                  # LLM service
│   │   ├── markdown_converter.py   # Docling integration for document conversion
│   │   ├── categorization.py       # AI-powered document categorization
│   │   ├── conversation.py         # Conversation context management
│   │   └── conversation_storage.py # SQLite-based conversation persistence
│   └── data/
│       └── conversations.db        # SQLite database for chat history
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── app-header.tsx           # Header with theme toggle
│       │   ├── chat-view.tsx            # Main chat interface
│       │   ├── conversation-history.tsx # Conversation sidebar
│       │   ├── documents-panel.tsx      # Documents management with category filtering
│       │   ├── category-badge.tsx       # Category display and filtering components
│       │   └── status-bar.tsx           # Status indicator
│       ├── hooks/
│       │   └── api.ts                   # React Query hooks
│       ├── lib/
│       │   ├── api.ts                   # API client
│       │   └── constants.ts             # Configuration
│       └── types/
│           └── index.ts                 # TypeScript types
├── docker/
│   └── docker-compose.yml          # Qdrant and optional full stack
└── README.md
```

## 📊 Performance Profiles

| Profile | CPU Usage | RAM Usage | Accuracy | Best For |
|--------:|-----------|-----------|----------|----------|
| Eco | Low | ~2GB | Good | Battery life, older laptops |
| Balanced | Medium | ~4GB | Better | Most users |
| Performance | High | ~8GB | Best | Powerful machines |

Set via env var:

```bash
export RAG_PROFILE=balanced
```

## 🔧 Development

### Backend

```bash
cd backend
pip install -e ".[dev]"

# Run tests
pytest

# Lint/format
black app/ tests/
isort app/ tests/
mypy app/

# Start API with auto-reload
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000

# Build
npm run build
```

## � Troubleshooting

**Qdrant connection failed**

```bash
curl http://localhost:6333/health
docker compose -f docker/docker-compose.yml restart qdrant
```

**Ollama model not found**

```bash
ollama list
ollama pull qwen2.5:7b-instruct
```

**Images not being processed / OCR not working**

- Set the `HF_TOKEN` environment variable with your HuggingFace token
- Create a token at https://huggingface.co/settings/tokens
- Add to `backend/.env`: `HF_TOKEN=your_token_here`
- Restart the backend server

**Frontend shows timeout (~30s) or slow status**

- Ensure both services are running (http://localhost:3000 and http://localhost:8000)
- Check `/api/status`: `curl http://localhost:8000/api/status`
- Make sure Ollama is serving and `RAG_LLM_MODEL` matches a pulled model
- Status health checks are capped to ~2s; if still slow, verify Qdrant and Ollama

**Out of memory errors**

```bash
export RAG_PROFILE=eco
export RAG_MAX_CONTEXT_TOKENS=2000
```

### Logs & Data

Application data (uploads, parsed, indices, logs) lives under `~/RAGApp/` by default.
Logs are written to `~/RAGApp/logs/app.jsonl`.

## 🔒 Security & Privacy

- Local processing: All operations happen on your machine
- No external cloud calls: Works fully offline (Ollama + Qdrant local)
- Optional encryption at rest and secure deletion supported
- No telemetry or tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Commit (`git commit -m "Describe your change"`)
4. Push (`git push origin feature/my-change`)
5. Open a Pull Request

## 📄 License

MIT — see [LICENSE](LICENSE).

## 🙏 Acknowledgments

- Qdrant — Vector similarity search
- Ollama — Local LLM runtime
- FastAPI — Python web framework
- Next.js — React framework
- Sentence Transformers — Embeddings

---

Built with privacy in mind — your documents stay local.
