"""
Ingest Galdunx knowledge-base into ChromaDB.
Uses the same DB path as answer.py so the chat app finds the collection.
Run from week5/IbrahimSheriff: python ingest.py
"""
import os
from pathlib import Path

import numpy  # Must be imported before HuggingFaceEmbeddings/SentenceTransformer use it

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

from dotenv import load_dotenv

load_dotenv(override=True)

# Same path as answer.py so both use the same vector store
DB_NAME = str(Path(__file__).parent / "vector_db")
KNOWLEDGE_BASE = str(Path(__file__).parent / "knowledge-base")

# Must match answer.py: OpenRouter or HuggingFace
if os.getenv("OPENROUTER_API_KEY"):
    embeddings = OpenAIEmbeddings(
        model="openai/text-embedding-3-small",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
    )
else:
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def fetch_documents():
    """Load all .md files from knowledge-base (flat or nested)."""
    loader = DirectoryLoader(
        KNOWLEDGE_BASE,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    return documents


def create_chunks(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=5, chunk_overlap=200)
    return text_splitter.split_documents(documents)


def create_embeddings(chunks):
    try:
        if os.path.exists(DB_NAME):
            Chroma(persist_directory=DB_NAME, embedding_function=embeddings).delete_collection()

        vectorstore = Chroma.from_documents(
            documents=chunks, embedding=embeddings, persist_directory=DB_NAME
        )
    except Exception as e:
        if "readonly" in str(e).lower() or "read-only" in str(e).lower():
            raise RuntimeError(
                "The vector database is locked because the Gradio chat app is still running.\n"
                "Stop the app first: interrupt the notebook kernel (e.g. click Stop), or close the\n"
                "Gradio tab and stop the server. Then re-run the ingest cell."
            ) from e
        if "Numpy is not available" in str(e):
            raise RuntimeError(
                "NumPy 2.x is incompatible with PyTorch in this setup. Either:\n"
                "  1. Set OPENROUTER_API_KEY in .env to use API embeddings, or\n"
                "  2. Run: uv pip install 'numpy<2' then re-run ingest."
            ) from e
        raise

    collection = vectorstore._collection
    count = collection.count()
    sample_embedding = collection.get(limit=1, include=["embeddings"])["embeddings"][0]
    dimensions = len(sample_embedding)
    print(f"There are {count:,} vectors with {dimensions:,} dimensions in the vector store")
    return vectorstore


if __name__ == "__main__":
    documents = fetch_documents()
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete.")
