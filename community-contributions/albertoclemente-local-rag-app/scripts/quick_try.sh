#!/usr/bin/env bash
set -euo pipefail

# Quick Try: start Qdrant (Docker), backend (FastAPI), and frontend (Next.js)
# Prereqs: docker, python, node, ollama

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# 1) Start Qdrant
if ! curl -sf http://localhost:6333/health >/dev/null 2>&1; then
  echo "[qdrant] starting via docker compose..."
  docker compose -f docker/docker-compose.yml up -d qdrant
  echo "[qdrant] waiting for health..."
  until curl -sf http://localhost:6333/health >/dev/null 2>&1; do sleep 2; done
fi

echo "[qdrant] healthy"

# 2) Ensure Ollama is running (best-effort)
if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "[ollama] starting background 'ollama serve' (if installed)..."
  (ollama serve >/dev/null 2>&1 &) || true
  sleep 2
fi

# 3) Start backend (reload)
(
  cd backend
  echo "[backend] installing (editable)"
  pip install -e . >/dev/null
  echo "[backend] starting uvicorn on :8000"
  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!

# 4) Start frontend
(
  cd frontend
  echo "[frontend] installing deps"
  npm install >/dev/null
  echo "[frontend] starting next dev on :3000"
  npm run dev
) &
FRONTEND_PID=$!

trap 'echo "Stopping..."; kill $BACKEND_PID $FRONTEND_PID >/dev/null 2>&1 || true' INT TERM

wait