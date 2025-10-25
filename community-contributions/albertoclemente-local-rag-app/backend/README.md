# Local RAG WebApp Backend

A local-only Retrieval-Augmented Generation (RAG) web application backend built with FastAPI.

## Features

- **Local-only processing**: No cloud API calls, everything runs locally
- **FastAPI backend**: RESTful API + WebSocket streaming
- **Vector search**: Qdrant integration for document embeddings
- **Adaptive chunking**: Intelligent document chunking based on content
- **Dynamic-k retrieval**: Adaptive number of chunks based on query
- **LLM streaming**: Real-time token streaming via WebSocket
- **Performance profiles**: Eco/Balanced/Performance modes

## Quick Start

### Prerequisites

- Python 3.9+
- Qdrant (via Docker or local binary)
- Ollama (for local LLM) or llama.cpp

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd RAG_APP/backend
```

2. Install dependencies:
```bash
pip install -e .
```

3. Start Qdrant:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

4. Start Ollama and pull a model:
```bash
ollama serve
ollama pull llama3.2:3b
```

5. Configure environment (optional):
```bash
cp .env.example .env
# Edit .env with your preferences
```

6. Run the server:
```bash
python -m app.main
# or
rag-server
```

The API will be available at `http://localhost:8000` with docs at `http://localhost:8000/api/docs`.

## Configuration

Set environment variables or create a `.env` file:

```bash
# Server
RAG_HOST=127.0.0.1
RAG_PORT=8000
RAG_DEBUG=false

# Performance profile
RAG_PROFILE=balanced  # eco|balanced|performance

# Data directory
RAG_DATA_DIR=~/RAGApp

# Services
QDRANT_URL=http://localhost:6333
OLLAMA_HOST=http://localhost:11434

# Models
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RAG_LLM_MODEL=llama3.2:3b

# RAG parameters
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=200
RAG_MAX_CONTEXT_TOKENS=4000
```

## API Endpoints

### Documents
- `POST /api/documents` - Upload document
- `GET /api/documents` - List documents
- `PATCH /api/documents/{doc_id}` - Update document metadata
- `DELETE /api/documents/{doc_id}` - Delete document
- `POST /api/documents/{doc_id}/reindex` - Reindex document

### Query
- `POST /api/query` - Start query (returns session/turn IDs for WebSocket)
- `WS /ws/stream?session_id=...&turn_id=...` - Stream response

### System
- `GET /api/settings` - Get current settings
- `PUT /api/settings` - Update settings
- `GET /api/status` - System status and resource usage
- `GET /health` - Health check

## Development

### Setup development environment:
```bash
pip install -e ".[dev]"
```

### Run tests:
```bash
pytest
```

### Code formatting:
```bash
black app/ tests/
isort app/ tests/
flake8 app/ tests/
mypy app/
```

### Run with auto-reload:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Architecture

The backend follows a modular architecture:

- `app/main.py` - FastAPI application setup and lifecycle
- `app/api.py` - REST API endpoints
- `app/ws.py` - WebSocket streaming handlers
- `app/models.py` - Pydantic data models
- `app/settings.py` - Configuration management
- `app/diagnostics.py` - Logging and monitoring

Additional modules (to be implemented):
- `app/storage.py` - File system operations
- `app/parsing.py` - Document text extraction
- `app/chunking.py` - Adaptive chunking algorithms
- `app/embeddings.py` - Local embedding generation
- `app/qdrant_index.py` - Vector store operations
- `app/retrieval.py` - RAG retrieval with dynamic-k
- `app/llm.py` - LLM inference and streaming
- `app/eval.py` - Evaluation utilities

## Performance Profiles

- **Eco**: Optimized for battery life and low resource usage
- **Balanced**: Default setting balancing performance and resources
- **Performance**: Maximum accuracy and speed, higher resource usage

## Security

- All processing happens locally
- No external API calls
- Optional encryption for stored documents
- Secure file deletion with overwrite option

## Troubleshooting

### Common issues:

1. **Qdrant connection failed**: Ensure Qdrant is running on port 6333
2. **Ollama not found**: Install and start Ollama service
3. **Out of memory**: Switch to Eco profile or reduce context budget
4. **Slow responses**: Check system resources, consider Performance profile

### Logging

Logs are written to `~/RAGApp/logs/app.jsonl` in structured JSON format.
Set `RAG_DEBUG=true` for verbose logging.

## License

MIT License - see LICENSE file for details.
