#!/usr/bin/env bash
set -euo pipefail

# Docker-only (backend + qdrant). Starts Qdrant and backend in containers.
# Ollama should run on the host at http://localhost:11434 (macOS/Windows supported via host.docker.internal).

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

docker compose -f docker/docker-compose.yml --profile full up -d

echo "Services running:"
docker compose -f docker/docker-compose.yml ps

echo "- Qdrant:  http://localhost:6333"
echo "- Backend:  http://localhost:8000"
echo "Note: Ensure Ollama is running on your host: 'ollama serve' and pull a model (e.g., 'ollama pull qwen2.5:7b-instruct')."
echo "(Frontend still runs locally: cd frontend && npm run build && npm run start, or use dev server npm run dev)"