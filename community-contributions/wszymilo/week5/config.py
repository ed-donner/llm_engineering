"""Configuration for RAG exercise. No .env; Ollama is assumed running."""

EMBEDDING_MODEL = "nomic-embed-text:v1.5"
LLM_MODEL = "ollama/granite4:tiny-h"

# Chunking (LLM output constraints)
CHUNK_MAX_CHARS = 400
CHUNK_OVERLAP_CHARS = 50

# Retrieval
RETRIEVAL_K = 20  # per query
FINAL_K = 10  # after rerank

FAISS_INDEX_DIR = "faiss_index"
