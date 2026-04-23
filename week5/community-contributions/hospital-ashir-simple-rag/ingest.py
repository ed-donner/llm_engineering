"""
Ingest the Hospital-Ashir knowledge base into a Chroma vector database.

The knowledge base lives in ./knowledge-base and is organized by folder:
    - hospital/   : general info about Ashir General Hospital
    - doctors/    : physician records
    - patients/   : patient case files
    - diseases/   : disease / condition programs

Each folder name is stored on the document as `doc_type` so that later retrieval
can filter by category (e.g. only search patient files).
"""

import os
import glob
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


BASE_DIR = Path(__file__).parent
KNOWLEDGE_BASE = str(BASE_DIR / "knowledge-base")
DB_NAME = str(BASE_DIR / "vector_db")

EMBEDDING_MODEL = "text-embedding-3-large"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

load_dotenv(override=True)

embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)


def fetch_documents():
    """Load every .md file under the knowledge-base folder and tag it with doc_type."""
    folders = glob.glob(str(Path(KNOWLEDGE_BASE) / "*"))
    documents = []

    for folder in folders:
        if not os.path.isdir(folder):
            continue

        doc_type = os.path.basename(folder)
        loader = DirectoryLoader(
            folder,
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        folder_docs = loader.load()

        for doc in folder_docs:
            doc.metadata["doc_type"] = doc_type
            doc.metadata["source_name"] = Path(doc.metadata.get("source", "")).stem
            documents.append(doc)

        print(f"Loaded {len(folder_docs):>3} documents from '{doc_type}/'")

    print(f"\nTotal documents loaded: {len(documents)}")
    return documents


def create_chunks(documents):
    """Split documents into overlapping chunks suitable for embedding."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = text_splitter.split_documents(documents)

    doc_types = sorted({chunk.metadata.get("doc_type", "unknown") for chunk in chunks})
    print(f"\nSplit into {len(chunks)} chunks across doc types: {doc_types}")
    return chunks


def create_embeddings(chunks):
    """(Re)build the Chroma vector store from the given chunks."""
    if os.path.exists(DB_NAME):
        print(f"\nDeleting existing collection at: {DB_NAME}")
        Chroma(
            persist_directory=DB_NAME,
            embedding_function=embeddings,
        ).delete_collection()

    print("Creating embeddings and writing to Chroma...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_NAME,
    )

    collection = vectorstore._collection
    count = collection.count()

    sample = collection.get(limit=1, include=["embeddings"])
    dimensions = len(sample["embeddings"][0]) if count else 0

    print(
        f"\nVector store ready: {count:,} vectors "
        f"({dimensions:,} dimensions each) persisted at '{DB_NAME}'."
    )
    return vectorstore


if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("\nIngestion complete.")
