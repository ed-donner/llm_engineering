"""Configuration for the Indie Publisher / Funding Matcher. All paths are inside this project (week8)."""
import os
from pathlib import Path

# Project root (indie-publisher-matcher folder)
MATCHER_ROOT = Path(__file__).resolve().parent

# OpenRouter (unified LLM API) – we use this instead of calling OpenAI directly
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
# OpenRouter model id, e.g. openai/gpt-4o-mini, anthropic/claude-3.5-sonnet
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

# Knowledge base: markdown files used to build the vector store (no Week 5 needed)
KNOWLEDGE_BASE_DIR = "game-publisher-kb"

# Chroma DB path: built from game-publisher-kb on first run if missing
DEFAULT_PUBLISHER_DB_PATH = MATCHER_ROOT / "game_publisher_db"
PUBLISHER_DB_PATH = Path(os.getenv("PUBLISHER_KB_DB_PATH", str(DEFAULT_PUBLISHER_DB_PATH)))

# Chunking for RAG (when building vector store)
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

# Minimum fit score (0-100) to consider an opportunity worth alerting
FIT_THRESHOLD = 60

# How many opportunities to score per run (top N from scanner)
MAX_OPPORTUNITIES_PER_RUN = 5
