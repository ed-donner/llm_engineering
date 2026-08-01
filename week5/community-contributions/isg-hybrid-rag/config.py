"""Configuration constants and clients for the RAG pipeline."""
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from chromadb import PersistentClient

load_dotenv(override=True)

# --- API / Model settings ---
API_KEY = "ollama"
MODEL   = "ollama_chat/ornith:9b"
URL     = "http://localhost:11434"

# --- Clients ---
OPENAI = OpenAI()
CLIENT = OpenAI(api_key=API_KEY, base_url=URL)

# --- ChromaDB ---
DB_NAME         = "preprocessed_db"
COLLECTION_NAME = "docs"
CHROMA          = PersistentClient(path=DB_NAME)

# --- Embeddings ---
EMBEDDING_MODEL = "text-embedding-3-large"

# --- Knowledge base ---
KNOWLEDGE_BASE_PATH = Path("week05/knowledge-base")

# --- Retrieval parameters ---
AVERAGE_CHUNK_SIZE   = 500
VECTOR_RETRIEVAL_K   = 15
KEYWORD_RETRIEVAL_K  = 10
ANSWER_CONTEXT_K     = 5

# --- Pipeline control ---
# Set to True to re-chunk and re-embed the knowledge base before answering.
REBUILD_DATABASE = False
