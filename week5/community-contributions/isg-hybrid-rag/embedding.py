"""Vector embedding generation and ChromaDB storage."""
from config import (
    OPENAI,
    COLLECTION_NAME,
    CHROMA,
    EMBEDDING_MODEL,
)


def create_embeddings(chunks):
    """Generate embeddings for chunks and store them in ChromaDB.

    If a collection with the given name already exists, it is deleted first.
    """
    if COLLECTION_NAME in [c.name for c in CHROMA.list_collections()]:
        CHROMA.delete_collection(COLLECTION_NAME)

    texts = [chunk.page_content for chunk in chunks]
    emb = OPENAI.embeddings.create(model=EMBEDDING_MODEL, input=texts).data
    vectors = [e.embedding for e in emb]

    collection = CHROMA.get_or_create_collection(COLLECTION_NAME)

    ids = [str(i) for i in range(len(chunks))]
    metas = [chunk.metadata for chunk in chunks]

    collection.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metas)
    print(f"Vectorstore created with {collection.count()} documents")
