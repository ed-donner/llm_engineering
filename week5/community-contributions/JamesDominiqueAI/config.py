"""
config.py — Central configuration for Regulatory Compliance RAG.

To switch AI models, edit the MODEL variable or set it in your .env file.
Supported providers via litellm: openai, groq, anthropic, ollama, and more.

FIX LOG:
- Increased RETRIEVAL_K from 20 → 30 and FINAL_K from 10 → 15
  to reduce the chance of keyword-relevant chunks being discarded after reranking.
- Increased DEFAULT_K from 10 → 15 and MAX_K from 30 → 40.
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "knowledge-base")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "preprocessed_db")
EVAL_RESULTS_DIR = os.path.join(BASE_DIR, "eval_results")

# ── Model Selection ────────────────────────────────────────────────────────────
# Change this (or set MODEL in .env) to switch providers instantly.
# litellm handles OpenAI, Groq, Anthropic, Ollama, etc. transparently.
#
# Examples:
#   "openai/gpt-4.1-nano"                    ← default (fast + cheap)
#   "openai/gpt-4o-mini"
#   "openai/gpt-4o"
#   "groq/llama-3.2-90b-text-preview"        ← very fast inference
#   "groq/llama-3.1-70b-versatile"
#   "groq/mixtral-8x7b-32768"
#   "anthropic/claude-3-haiku-20240307"
#   "anthropic/claude-3-5-sonnet-20241022"
MODEL = os.getenv("MODEL", "openai/gpt-4o-mini")

# ── API Keys ───────────────────────────────────────────────────────────────────
# Set in .env file or as environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ── Embedding Model ────────────────────────────────────────────────────────────
# Always uses OpenAI for embeddings (best quality, consistent vector space)
EMBEDDING_MODEL = "text-embedding-3-large"

# ── ChromaDB ───────────────────────────────────────────────────────────────────
COLLECTION_NAME = "docs"

# ── Ingestion ──────────────────────────────────────────────────────────────────
AVERAGE_CHUNK_SIZE = 500        # Hint to LLM for how many chunks to create
INGEST_WORKERS = 3              # Parallel workers for document processing
                                # Set to 1 if you hit rate limits

# ── Retrieval ──────────────────────────────────────────────────────────────────
# Increased from 20→30 and 10→15 to reduce relevant chunk loss after reranking.
RETRIEVAL_K = 30                # Chunks fetched per retrieval call (before rerank)
FINAL_K = 15                    # Chunks passed to answer generation after rerank
DEFAULT_K = 15                  # Starting k for adaptive loop
MAX_K = 40                      # Maximum k in adaptive loop
ADAPTIVE_MAX_ATTEMPTS = 3
CONFIDENCE_THRESHOLD = 0.75
MIN_CONFIDENCE_FOR_REWRITE = 0.4

# ── Retry (tenacity) ───────────────────────────────────────────────────────────
RETRY_MIN_WAIT = 10             # seconds
RETRY_MAX_WAIT = 240            # seconds
