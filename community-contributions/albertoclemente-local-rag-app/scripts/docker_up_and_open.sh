#!/usr/bin/env bash
set -euo pipefail

# One-click: build and start full Docker stack, then open the app.
# macOS zsh-friendly. Requires Docker Desktop and Ollama (on host).

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# Ensure Docker CLI is available (common on macOS when launched from GUI)
if ! command -v docker >/dev/null 2>&1; then
  if [ -x "/Applications/Docker.app/Contents/Resources/bin/docker" ]; then
    export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
  fi
fi

# Start Docker Desktop if not running (best-effort on macOS)
if ! docker info >/dev/null 2>&1; then
  echo "Starting Docker Desktop..."
  open -g -a Docker || true
  # Wait for Docker to be ready
  until docker info >/dev/null 2>&1; do
    printf '.'; sleep 2
  done
  echo ""
fi

# Build and start
echo "Building images (frontend, backend) and starting services..."
docker compose -f docker/docker-compose.yml --profile full build
# Qdrant may start faster than backend; let compose handle ordering
docker compose -f docker/docker-compose.yml --profile full up -d

echo "Services status:"
docker compose -f docker/docker-compose.yml --profile full ps

echo "Ensuring Ollama is running on host (http://localhost:11434)..."
if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "Starting 'ollama serve' in background (if installed)..."
  (ollama serve >/dev/null 2>&1 &) || true
  sleep 2
fi

echo "Waiting for frontend to be reachable at http://localhost:3000 ..."
until curl -sf http://localhost:3000 >/dev/null 2>&1; do
  sleep 2
  printf '.'
done
echo ""

# Open in default browser (macOS 'open')
if command -v open >/dev/null 2>&1; then
  open http://localhost:3000
fi

echo "All set! UI: http://localhost:3000 | API: http://localhost:8000 | Qdrant: http://localhost:6333"