# Price Is Right - Host-Based Setup

A simplified host-based microservices implementation of "The Price is Right" deal hunting system.

## Overview

This setup runs all services directly on the host without Docker containers, using a shared Python virtual environment and direct Ollama connection.

## Prerequisites

- Python 3.11+
- Ollama running on port 11434
- Required Ollama models: `llama3.2` and `llama3.2:3b-instruct-q4_0`

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # or with uv:
   uv pip install -r requirements.txt
   ```

2. **Start all services:**
   ```bash
   python service_manager.py start
   ```

3. **Access the UI:**
   - Main UI: http://localhost:7860
   - Notification Receiver: http://localhost:7861

4. **Stop all services:**
   ```bash
   python service_manager.py stop
   ```

## Service Architecture

| Service | Port | Description |
|---------|------|-------------|
| Scanner Agent | 8001 | Scans for deals from RSS feeds |
| Specialist Agent | 8002 | Fine-tuned LLM price estimation |
| Frontier Agent | 8003 | RAG-based price estimation |
| Random Forest Agent | 8004 | ML model price prediction |
| Ensemble Agent | 8005 | Combines all price estimates |
| Planning Agent | 8006 | Orchestrates deal evaluation |
| Notification Service | 8007 | Sends deal alerts |
| Notification Receiver | 8008 | Receives and displays alerts |
| UI | 7860 | Main web interface |

## Service Management

### Start Services
```bash
# Start all services
python service_manager.py start

# Start specific service
python service_manager.py start scanner
```

### Stop Services
```bash
# Stop all services
python service_manager.py stop

# Stop specific service
python service_manager.py stop scanner
```

### Check Status
```bash
python service_manager.py status
```

### Restart Service
```bash
python service_manager.py restart scanner
```

## Data Files

- `data/models/` - Contains .pkl model files (immediately accessible)
- `data/vectorstore/` - ChromaDB vector store
- `data/memory.json` - Deal memory storage
- `logs/` - Service log files

## Key Features

- **No Docker overhead** - Services start instantly
- **Direct file access** - .pkl files load immediately
- **Single environment** - All services share the same Python environment
- **Direct Ollama access** - No proxy needed
- **Easy debugging** - Direct process access and logs

## Troubleshooting

1. **Port conflicts**: Check if ports are already in use
   ```bash
   python service_manager.py status
   ```

2. **Ollama connection issues**: Ensure Ollama is running on port 11434
   ```bash
   ollama list
   ```

3. **Service logs**: Check individual service logs in `logs/` directory

4. **Model loading**: Ensure required models are available
   ```bash
   ollama pull llama3.2
   ollama pull llama3.2:3b-instruct-q4_0
   ```

## Development

- All services are in `services/` directory
- Shared code is in `shared/` directory
- Service manager handles process lifecycle
- Logs are written to `logs/` directory
