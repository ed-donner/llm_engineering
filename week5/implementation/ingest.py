from pathlib import Path
import re

import ollama
from chromadb import PersistentClient
from tqdm import tqdm


BASE_DIR = Path(__file__).resolve().parent.parent

KNOWLEDGE_BASE_PATH = BASE_DIR / "knowledge-base"
DB_NAME = str(BASE_DIR / "vector_db")

COLLECTION_NAME = "docs"
EMBED_MODEL = "nomic-embed-text:latest"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def load_documents():
    documents = []

    for folder in KNOWLEDGE_BASE_PATH.iterdir():
        if not folder.is_dir():
            continue

        doc_type = folder.name

        for file in folder.rglob("*.md"):
            text = file.read_text(encoding="utf-8")

            documents.append(
                {
                    "source": file.as_posix(),
                    "type": doc_type,
                    "text": text,
                }
            )

    print(f"Loaded {len(documents)} documents")
    return documents


def split_text(text):
    text = re.sub(r"\n{3,}", "\n\n", text.strip())

    paragraphs = text.split("\n\n")

    chunks = []
    current = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        if len(current) + len(paragraph) + 2 <= CHUNK_SIZE:
            current += ("\n\n" if current else "") + paragraph
        else:
            if current:
                chunks.append(current)

            overlap = current[-CHUNK_OVERLAP:] if current else ""
            current = overlap + "\n\n" + paragraph

    if current:
        chunks.append(current)

    return chunks


def create_chunks(documents):
    chunks = []

    for document in documents:
        text_chunks = split_text(document["text"])

        for chunk in text_chunks:
            chunks.append(
                {
                    "text": chunk,
                    "metadata": {
                        "source": document["source"],
                        "type": document["type"],
                    },
                }
            )

    return chunks


def get_embedding(text):
    response = ollama.embeddings(
        model=EMBED_MODEL,
        prompt=text,
    )

    return response["embedding"]


def create_vector_database(chunks):
    chroma = PersistentClient(path=DB_NAME)

    # Remove old collection so old OpenAI embeddings are not reused.
    existing = [collection.name for collection in chroma.list_collections()]

    if COLLECTION_NAME in existing:
        chroma.delete_collection(COLLECTION_NAME)

    collection = chroma.get_or_create_collection(COLLECTION_NAME)

    print(f"Creating {len(chunks)} local embeddings...")

    for index, chunk in enumerate(
        tqdm(chunks, desc="Creating embeddings")
    ):
        embedding = get_embedding(chunk["text"])

        collection.add(
            ids=[str(index)],
            embeddings=[embedding],
            documents=[chunk["text"]],
            metadatas=[chunk["metadata"]],
        )

    print()
    print("Vector database created successfully.")
    print(f"Documents: {collection.count()}")
    print(f"Database: {DB_NAME}")


def main():
    documents = load_documents()

    if not documents:
        raise RuntimeError(
            f"No Markdown files found in {KNOWLEDGE_BASE_PATH}"
        )

    chunks = create_chunks(documents)

    print(f"Created {len(chunks)} chunks")

    create_vector_database(chunks)

    print("Ingestion complete!")


if __name__ == "__main__":
    main()