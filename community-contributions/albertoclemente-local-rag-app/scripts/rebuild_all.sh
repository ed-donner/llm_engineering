#!/usr/bin/env bash
set -euo pipefail

# Rebuild all services without cache and start the stack
# Usage: ./scripts/rebuild_all.sh [--no-start]

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
COMPOSE_FILE="$ROOT_DIR/docker/docker-compose.yml"
# Avoid quoting inside the variable to prevent duplicated literal quotes
COMPOSE=(docker compose -f "$COMPOSE_FILE")

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker not found in PATH. Please install/start Docker Desktop and try again." >&2
  exit 127
fi

# Guard: Port 3000 must be free (frontend binds to it)
if command -v lsof >/dev/null 2>&1; then
  if lsof -i :3000 >/dev/null 2>&1; then
    echo "Error: Port 3000 is in use. Please stop any dev server (npm run dev) and retry." >&2
    exit 1
  fi
fi

# Stop existing stack if running
( "${COMPOSE[@]}" down --remove-orphans || true )

# Rebuild images without cache
"${COMPOSE[@]}" --profile full build --no-cache

# Start full stack (including frontend)
if [[ "${1:-}" != "--no-start" ]]; then
  "${COMPOSE[@]}" --profile full up -d --remove-orphans
  echo "\nStack is starting. Useful ports:"
  echo "- Frontend: http://localhost:3000"
  echo "- Backend API: http://localhost:8000/api"
  echo "- Qdrant: http://localhost:6333"
fi
