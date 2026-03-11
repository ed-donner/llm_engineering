"""
Ingest knowledge_base markdown docs into Chroma using HuggingFaceEmbeddings.
Load .env from project root. Run from repo root or from this directory.
"""
from pathlib import Path

# Load .env from project root (llm_engineering)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DOTENV = PROJECT_ROOT / ".env"
if DOTENV.exists():
    from dotenv import load_dotenv
    load_dotenv(DOTENV, override=True)

from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer

MAKINDA_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE = MAKINDA_DIR / "knowledge_base"
DB_PATH = MAKINDA_DIR / "vector_db"
COLLECTION_NAME = "kuccps_docs"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

# Local embedding model (no API key required)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def load_documents():
    """Load all .md files from knowledge_base into a list of (text, source) tuples."""
    docs = []
    for path in KNOWLEDGE_BASE.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        source = path.relative_to(MAKINDA_DIR).as_posix()
        docs.append((text, source))
    return docs


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks (by character count)."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if end < len(text):
            # Try to break at a sentence or newline
            last_newline = chunk.rfind("\n")
            if last_newline > chunk_size // 2:
                chunk = chunk[: last_newline + 1]
                end = start + last_newline + 1
        chunks.append(chunk.strip())
        start = end - overlap if overlap < chunk_size else end
    return [c for c in chunks if c]


def main():
    docs = load_documents()
    if not docs:
        print("No .md files found in knowledge_base/")
        return

    all_chunks = []
    all_metas = []
    for text, source in docs:
        for chunk in chunk_text(text):
            all_chunks.append(chunk)
            all_metas.append({"source": source})

    print(f"Loaded {len(docs)} documents, {len(all_chunks)} chunks")

    # Embed with SentenceTransformer (local, no API key)
    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = model.encode(all_chunks).tolist()

    client = PersistentClient(path=str(DB_PATH))
    if COLLECTION_NAME in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION_NAME)
    collection = client.create_collection(name=COLLECTION_NAME)

    collection.add(
        ids=[str(i) for i in range(len(all_chunks))],
        embeddings=embeddings,
        documents=all_chunks,
        metadatas=all_metas,
    )
    print(f"Vector store created at {DB_PATH} with {collection.count()} chunks")


if __name__ == "__main__":
    main()
