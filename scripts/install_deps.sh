#!/usr/bin/env bash
# Install all dependencies for llm_engineering.
# Run from repo root: bash scripts/install_deps.sh

set -e
cd "$(dirname "$0")/.."

echo "=== Installing dependencies for llm_engineering ==="

if command -v uv &>/dev/null; then
  echo "Using uv..."
  uv self update 2>/dev/null || true
  uv sync
  echo "Done. Use: uv run python ... or uv run jupyter lab"
  exit 0
fi

echo "uv not found. Using pip + venv..."
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Done. Activate with: source .venv/bin/activate"
