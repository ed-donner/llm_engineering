"""
ingest/embedder.py — Embeds chunks using OpenAI text-embedding-3-large and stores
them in a persistent ChromaDB collection.
"""

import os
import sys
from typing import List
from openai import OpenAI
from chromadb import PersistentClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EMBEDDING_MODEL, CHROMA_DB_DIR, COLLECTION_NAME, OPENAI_API_KEY
from ingest.chunker import Result, fetch_documents, create_chunks

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def get_chroma_collection():
    """Return (or create) the ChromaDB persistent collection."""
    client = PersistentClient(path=CHROMA_DB_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def create_embeddings(chunks: List[Result], force_reingest: bool = False) -> None:
    """
    Embed all chunks using OpenAI text-embedding-3-large and upsert into ChromaDB.
    Deletes existing collection first if force_reingest=True.
    """
    chroma = PersistentClient(path=CHROMA_DB_DIR)

    if force_reingest:
        if COLLECTION_NAME in [c.name for c in chroma.list_collections()]:
            chroma.delete_collection(COLLECTION_NAME)
            print(f"[Embedder] Deleted existing collection '{COLLECTION_NAME}'")

    collection = chroma.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [chunk.page_content for chunk in chunks]
    metas = [chunk.metadata for chunk in chunks]
    ids = [str(i) for i in range(len(chunks))]

    print(f"[Embedder] Embedding {len(texts)} chunks with {EMBEDDING_MODEL}...")

    # Batch embed to respect API limits
    batch_size = 100
    all_vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i: i + batch_size]
        print(f"[Embedder] Batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1} "
              f"({len(batch)} chunks)...")
        response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        all_vectors.extend([e.embedding for e in response.data])

    collection.add(ids=ids, embeddings=all_vectors, documents=texts, metadatas=metas)
    print(f"[Embedder] ✅ Vectorstore created with {collection.count()} chunks")


def build_index(force_reingest: bool = False) -> None:
    """Full pipeline: load documents → LLM chunk → embed → store."""
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks, force_reingest=force_reingest)


if __name__ == "__main__":
    build_index(force_reingest=True)
    print("Ingestion complete")

