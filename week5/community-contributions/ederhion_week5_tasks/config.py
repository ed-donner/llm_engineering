# config.py
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).parent
DB_NAME = str(BASE_DIR / "vector_db")
KNOWLEDGE_BASE = str(BASE_DIR / "knowledge-base")

# Model Configurations
LLM_MODEL = "openai/gpt-4o"
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
RERANKER_MODEL = "BAAI/bge-reranker-large"

# Hardware Configuration
# Options: "cpu", "cuda" (Nvidia GPU), or "mps" (Apple Silicon)
DEVICE = "cpu" 

# Cloud Sync
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1O7lUf0oXEiFsltSc21Q4Hw_X2pUJpLxL"

# Prompts
SYSTEM_PROMPT = """
You are an expert Enterprise Database Engineering Assistant.
You have perfectly memorized the official Oracle Database documentation.
Use the provided retrieved context to answer the user's architectural, performance tuning, or troubleshooting question.
When providing code or PL/SQL (Procedural Language/Structured Query Language), ensure it is highly optimized.
Always cite the source manual and page number provided in the context.
If the answer is not contained within the context, explicitly state that you do not know.

Context:
{context}
"""