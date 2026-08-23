#!/usr/bin/env python3
"""
Build a ChromaDB vector store for SEC filings and financial documents.
Reads from knowledge_base/filings/ or generates sample data for MVP.
"""

import os
import re
from pathlib import Path
from typing import List, Dict

import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Add haastrupea root for imports
import sys

base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

try:
    from helpers.config import DB_PATH, COLLECTION_NAME, KNOWLEDGE_BASE, MODEL_NAME
except ImportError:
    DB_PATH = str(base_dir / "research_vectorstore")
    COLLECTION_NAME = "filings"
    KNOWLEDGE_BASE = str(base_dir / "knowledge_base" / "filings")
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    """Split text into overlapping chunks (approximate token count)."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def load_filings_from_dir(kb_path: str) -> List[Dict]:
    """Load .txt files from knowledge_base/filings/. Filenames: ticker_doc_type.txt"""
    documents = []
    path = Path(kb_path)
    if not path.exists():
        return []
    for f in path.glob("*.txt"):
        name = f.stem
        parts = name.split("_", 1)
        ticker = parts[0].upper() if parts else "UNKNOWN"
        doc_type = parts[1] if len(parts) > 1 else "filing"
        content = f.read_text(encoding="utf-8", errors="ignore")
        for i, chunk in enumerate(chunk_text(content)):
            documents.append(
                {
                    "text": chunk,
                    "ticker": ticker,
                    "doc_type": doc_type,
                    "filing_date": "2024-01-01",
                    "id": f"{ticker}_{doc_type}_{i}",
                }
            )
    return documents


def generate_sample_filings() -> List[Dict]:
    """Generate sample filing chunks for MVP when knowledge_base is empty."""
    samples = [
        ("AAPL", "10-K", "Apple Inc. designs and manufactures consumer electronics, software, and services. "
         "Key products include iPhone, Mac, iPad, Apple Watch, and services such as the App Store and iCloud. "
         "Revenue for fiscal 2024 was approximately $390 billion. The company continues to invest in R&D for AI and AR."),
        ("AAPL", "10-K", "Apple's services segment includes advertising, App Store, AppleCare, cloud, digital content, and payment services. "
         "Services gross margin is higher than product gross margin. Geographic segments include Americas, Europe, Greater China, Japan, and Rest of Asia Pacific."),
        ("GOOGL", "10-Q", "Alphabet Inc. operates Google Search, YouTube, Android, Google Cloud, and Other Bets. "
         "Google Cloud Platform and Workspace are key growth drivers. Advertising revenue remains the primary revenue source."),
        ("MSFT", "10-K", "Microsoft Corporation develops and supports software, services, devices, and solutions. "
         "Segments include Productivity and Business Processes, Intelligent Cloud, and More Personal Computing. "
         "Azure and Office 365 are major revenue drivers."),
        ("AMZN", "10-Q", "Amazon.com operates e-commerce, AWS, advertising, and subscription services. "
         "AWS provides cloud computing. North America and International segments each contribute significant revenue."),
        ("NVDA", "10-Q", "NVIDIA Corporation designs GPUs for gaming, professional visualization, data center, and automotive. "
         "Data center segment revenue grew significantly due to AI and machine learning demand. Gaming and professional visualization also contribute."),
    ]
    docs = []
    for ticker, doc_type, text in samples:
        for i, chunk in enumerate(chunk_text(text, chunk_size=80)):
            docs.append({
                "text": chunk,
                "ticker": ticker,
                "doc_type": doc_type,
                "filing_date": "2024-01-01",
                "id": f"{ticker}_{doc_type}_sample_{i}",
            })
    return docs


def build():
    os.makedirs(DB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME, metadata={"description": "SEC filings and financial docs"})

    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    documents = load_filings_from_dir(KNOWLEDGE_BASE)
    if not documents:
        print("No files in knowledge_base/filings/. Using sample data.")
        documents = generate_sample_filings()

    ids = [d["id"] for d in documents]
    texts = [d["text"] for d in documents]
    metadatas = [{"ticker": d["ticker"], "doc_type": d["doc_type"], "filing_date": d["filing_date"]} for d in documents]

    print(f"Encoding {len(documents)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True)

    collection.add(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=embeddings.tolist(),
    )
    print(f"Added {len(documents)} chunks to {DB_PATH}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build filings vector store")
    parser.add_argument("--rebuild", action="store_true", help="Clear and rebuild")
    args = parser.parse_args()
    if args.rebuild:
        path = Path(DB_PATH)
        if path.exists():
            import shutil
            shutil.rmtree(DB_PATH)
            print("Cleared existing vector store")
    build()


if __name__ == "__main__":
    main()
