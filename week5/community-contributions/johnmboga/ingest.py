"""
ingest.py - Ingest legal documents into ChromaDB vector store
Run this once to populate the database before starting the app.
"""

import os
import glob
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

DATA_DIR = "./sample_data"
CHROMA_DIR = "./chroma_db"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
EMBEDDING_MODEL = "text-embedding-3-large"
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
os.environ["OPENAI_API_KEY"] = openrouter_api_key
openrouter_base_url = "https://openrouter.ai/api/v1"

def load_documents(data_dir: str):
    """Load all .txt and .pdf files from the data directory."""
    docs = []

    # Load .txt files
    for fp in glob.glob(os.path.join(data_dir, "**/*.txt"), recursive=True):
        loader = TextLoader(fp, encoding="utf-8")
        loaded = loader.load()
        for doc in loaded:
            doc.metadata["source"] = Path(fp).name
            doc.metadata["file_type"] = "txt"
        docs.extend(loaded)
        print(f"  ✓ Loaded: {Path(fp).name} ({len(loaded)} document(s))")

    # Load .pdf files
    for fp in glob.glob(os.path.join(data_dir, "**/*.pdf"), recursive=True):
        loader = PyPDFLoader(fp)
        loaded = loader.load()
        for doc in loaded:
            doc.metadata["source"] = Path(fp).name
            doc.metadata["file_type"] = "pdf"
        docs.extend(loaded)
        print(f"  ✓ Loaded: {Path(fp).name} ({len(loaded)} page(s))")

    return docs

def chunk_documents(docs):
    """Split documents into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks = splitter.split_documents(docs)

    doc_chunk_counts = {}

    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        doc_chunk_counts.setdefault(source, 0)

        chunk.metadata["chunk_id"] = doc_chunk_counts[source]
        chunk.metadata["document"] = source

        doc_chunk_counts[source] += 1

    print(f"\n  → Split into {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    return chunks

def ingest(docs):
    """
    Ingest the given documents into ChromaDB.
    Chunks the docs and adds them to the vector store.

    Args:
        docs: List of LangChain Documents to ingest.

    Returns:
        Tuple of (chunks, source_summaries) for the caller to use.
    """
    chunks = chunk_documents(docs)
    if not chunks:
        return [], []

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=openrouter_api_key,
        base_url=openrouter_base_url
    )
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name="kenya_legal_docs"
    )
    vectorstore.add_documents(chunks)
    print(f"\n✅ Done! {len(chunks)} chunks stored in '{CHROMA_DIR}'")
    print("   Run `python app.py` to start the assistant.\n")

    from collections import Counter
    source_counts = Counter(c.metadata.get("source", "unknown") for c in chunks)
    source_summaries = [f"✓ {src} ({count} chunks)" for src, count in source_counts.items()]
    return chunks, source_summaries

if __name__ == "__main__":
    docs = load_documents(DATA_DIR)
    print(f"There are {len(docs)} documents in the vector store")
    ingest(docs)

