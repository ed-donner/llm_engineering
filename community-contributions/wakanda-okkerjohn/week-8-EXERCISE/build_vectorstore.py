"""
Build the Chroma vector store from game-publisher-kb markdown files.

Runs automatically when the RAG agent needs the DB and it doesn't exist.
Can also be run manually: python build_vectorstore.py
"""
import logging
import uuid
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from config import KNOWLEDGE_BASE_DIR, PUBLISHER_DB_PATH, CHUNK_SIZE, CHUNK_OVERLAP

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


def _load_documents() -> list[tuple[str, str]]:
    """Load all .md files under KNOWLEDGE_BASE_DIR. Returns list of (text, doc_type)."""
    base = Path(__file__).resolve().parent / KNOWLEDGE_BASE_DIR
    if not base.exists():
        raise FileNotFoundError(f"Knowledge base not found: {base}")
    docs = []
    for md_path in base.rglob("*.md"):
        rel = md_path.relative_to(base)
        doc_type = rel.parts[0] if len(rel.parts) > 1 else "root"
        text = md_path.read_text(encoding="utf-8").strip()
        if text:
            docs.append((text, doc_type))
    return docs


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
        if start >= len(text):
            break
    return chunks


def build() -> Path:
    """
    Load game-publisher-kb, chunk, embed with SentenceTransformer, store in Chroma.
    Returns the path to the DB.
    """
    LOG.info("Loading documents from %s", KNOWLEDGE_BASE_DIR)
    raw_docs = _load_documents()
    all_chunks = []
    all_metas = []
    for text, doc_type in raw_docs:
        for chunk in _chunk_text(text):
            all_chunks.append(chunk)
            all_metas.append({"doc_type": doc_type})

    if not all_chunks:
        raise ValueError("No chunks produced from knowledge base")

    LOG.info("Embedding %d chunks with SentenceTransformer", len(all_chunks))
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    embeddings = model.encode(all_chunks).tolist()

    PUBLISHER_DB_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(PUBLISHER_DB_PATH))
    collection_name = "publisher_kb"
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.create_collection(name=collection_name, metadata={"description": "Game publisher KB"})
    ids = [str(uuid.uuid4()) for _ in all_chunks]
    collection.add(ids=ids, embeddings=embeddings, documents=all_chunks, metadatas=all_metas)
    LOG.info("Vector store built: %d chunks in %s", len(all_chunks), PUBLISHER_DB_PATH)
    return PUBLISHER_DB_PATH


if __name__ == "__main__":
    build()
