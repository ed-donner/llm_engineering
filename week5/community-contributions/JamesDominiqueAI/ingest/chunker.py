# chunker.py
"""
ingest/chunker.py — LLM-based document chunking with multiprocessing.

Sends each regulation document to the LLM, which intelligently splits it
into overlapping chunks with a headline, summary, and original text.
Uses multiprocessing for parallel processing and tenacity for retries.
"""

import os
import sys
from pathlib import Path
from multiprocessing import Pool
from typing import List
from tqdm import tqdm
from pydantic import BaseModel, Field
from tenacity import retry, wait_exponential

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    KNOWLEDGE_BASE_DIR, MODEL, AVERAGE_CHUNK_SIZE,
    INGEST_WORKERS, RETRY_MIN_WAIT, RETRY_MAX_WAIT,
)
from utils.json_completion import json_completion

wait = wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT)


# ── Data Models ────────────────────────────────────────────────────────────────

class Result(BaseModel):
    """A single retrievable chunk — mirrors LangChain's Document structure."""
    page_content: str
    metadata: dict


class Chunk(BaseModel):
    """A single chunk as extracted by the LLM."""
    headline: str = Field(
        description="A brief heading for this chunk, typically a few words, "
                    "that is most likely to be surfaced in a query"
    )
    summary: str = Field(
        description="A few sentences summarizing the content of this chunk to answer common questions"
    )
    original_text: str = Field(
        description="The original text of this chunk from the provided document, "
                    "exactly as is, not changed in any way"
    )

    def as_result(self, document: dict) -> Result:
        metadata = {
            "source": document["source"],
            "type": document["type"],
        }
        return Result(
            page_content=self.headline + "\n\n" + self.summary + "\n\n" + self.original_text,
            metadata=metadata,
        )


class Chunks(BaseModel):
    chunks: List[Chunk]


# ── Document Loading ───────────────────────────────────────────────────────────

def fetch_documents() -> List[dict]:
    """
    Walk the knowledge-base directory and load all .md files.
    Folder name becomes the doc_type (regulations, amendments, guidance, audit_reports).
    """
    documents = []
    kb_path = Path(KNOWLEDGE_BASE_DIR)

    for folder in kb_path.iterdir():
        if not folder.is_dir():
            continue
        doc_type = folder.name
        for file in folder.rglob("*.md"):
            with open(file, "r", encoding="utf-8") as f:
                documents.append({
                    "type": doc_type,
                    "source": file.as_posix(),
                    "text": f.read(),
                })

    print(f"[Chunker] Loaded {len(documents)} documents from {KNOWLEDGE_BASE_DIR}")
    return documents


# ── LLM Chunking ──────────────────────────────────────────────────────────────

def make_prompt(document: dict) -> str:
    how_many = (len(document["text"]) // AVERAGE_CHUNK_SIZE) + 1
    return f"""
You take a document and split it into overlapping chunks for a Knowledge Base.

The document is of type: {document["type"]}
The document has been retrieved from: {document["source"]}

A chatbot will use these chunks to answer regulatory compliance questions.
Divide the document so that each chunk can independently answer specific questions.
This document should be split into at least {how_many} chunks, but use more if needed.
There should be ~25% overlap between adjacent chunks (~50 words) for better retrieval.

For each chunk provide:
- headline: A brief heading most likely to be surfaced in a query
- summary: A few sentences summarizing the chunk content
- original_text: The original text exactly as-is, unchanged

Your chunks together must represent the entire document with overlap. Don't leave anything out.

Here is the document:

{document["text"]}

Respond with the chunks.
"""


def make_messages(document: dict) -> List[dict]:
    return [{"role": "user", "content": make_prompt(document)}]


@retry(wait=wait)
def process_document(document: dict) -> List[Result]:
    """Send one document to the LLM for intelligent chunking. Retries on failure."""
    messages = make_messages(document)
    doc_chunks = json_completion(MODEL, messages, Chunks).chunks
    return [chunk.as_result(document) for chunk in doc_chunks]


def create_chunks(documents: List[dict]) -> List[Result]:
    """
    Process all documents in parallel using multiprocessing.
    Set INGEST_WORKERS=1 in config.py if you hit rate limits.
    """
    all_chunks = []
    with Pool(processes=INGEST_WORKERS) as pool:
        for result in tqdm(
            pool.imap_unordered(process_document, documents),
            total=len(documents),
            desc="Chunking documents",
        ):
            all_chunks.extend(result)
    print(f"[Chunker] Created {len(all_chunks)} chunks from {len(documents)} documents")
    return all_chunks


if __name__ == "__main__":
    docs = fetch_documents()
    chunks = create_chunks(docs)
    for c in chunks[:2]:
        print(f"\n{'='*60}")
        print(f"Source: {c.metadata['source']}")
        print(f"Preview: {c.page_content[:300]}")