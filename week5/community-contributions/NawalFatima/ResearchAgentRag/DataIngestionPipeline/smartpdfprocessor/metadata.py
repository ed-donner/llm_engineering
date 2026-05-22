import hashlib
from pathlib import Path
from datetime import datetime


def build_metadata(
    pdf_path: str,
    tier: str,
    author: str = "",
    title: str = "",
    document_type: str = "book",
) -> dict:
    """
    Base metadata for rich tier chunks.
    LLM-generated fields (section_title, topic, summary, page_start, page_end)
    are merged in by chunker.chunk() after LLM response.
    """
    document_id = hashlib.md5(pdf_path.encode()).hexdigest()

    return {
        "source": pdf_path,
        "document_id": document_id,
        "tier": tier,
        "author": author,
        "title": title,
        "document_type": document_type,
        "ingested_at": datetime.now().isoformat(),
    }


def build_fast_metadata(
    pdf_path: str,
    document_type: str = "book",
    author: str = "",
    title: str = "",
) -> dict:
    """
    Base metadata for fast tier chunks.
    LLM-generated fields are merged in by chunker.chunk().
    """
    document_id = hashlib.md5(pdf_path.encode()).hexdigest()

    return {
        "source": pdf_path,
        "document_id": document_id,
        "tier": "fast",
        "author": author,
        "title": title,
        "document_type": document_type,
        "ingested_at": datetime.now().isoformat(),
    }