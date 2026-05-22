"""
ingest.py — PDF ingestion pipeline

Processes PDFs through SmartPDFProcessor and stores embeddings
in ChromaDB (Cloud or local) using OpenAI text-embedding-3-small.

Two entry points:
    1. Terminal:  python ingest.py --pdf attention.pdf --enrich
    2. Import:    from ingest import ingest_pdf, quick_search

Functions can be used from notebooks, FastAPI, or any Python code.
Terminal argparse is a convenience wrapper around the same functions.
"""

import argparse
import logging
import os
import time
import chromadb
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from DataIngestionPipeline.smartpdfprocessor import SmartPDFProcessor
from DataIngestionPipeline.smartpdfprocessor.enrichment import enrich as enrich_chunks
from DataIngestionPipeline.smartpdfprocessor.equation_extractor import EquationExtractor

_equation_extractor = EquationExtractor()

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  CONFIG                                                              #
# ------------------------------------------------------------------ #

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CHROMA_TENANT = os.getenv("CHROMA_TENANT", "")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE", "")
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY", "")

EMBEDDING_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "research_brain"


# ------------------------------------------------------------------ #
#  EMBEDDING MODEL                                                     #
# ------------------------------------------------------------------ #

def get_embedding_model():
    """
    OpenAI text-embedding-3-small.
    $0.02 per 1M tokens — pennies for entire books.
    """
    logger.info("Loading OpenAI embedding model...")
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=OPENAI_API_KEY,
    )


# ------------------------------------------------------------------ #
#  VECTOR STORE                                                        #
# ------------------------------------------------------------------ #

def get_vector_store(embeddings):
    """
    Returns a ChromaDB Cloud vector store.
    Raises if credentials are missing.
    """
    if not CHROMA_TENANT or not CHROMA_API_KEY:
        raise EnvironmentError(
            "ChromaDB Cloud credentials missing. Set CHROMA_TENANT and CHROMA_API_KEY in .env"
        )

    logger.info(f"Connecting to ChromaDB Cloud — tenant: {CHROMA_TENANT}, db: {CHROMA_DATABASE}")
    client = chromadb.CloudClient(
        tenant=CHROMA_TENANT,
        database=CHROMA_DATABASE,
        api_key=CHROMA_API_KEY,
    )
    vector_store = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )
    logger.info(f"ChromaDB ready — collection: {COLLECTION_NAME}")
    return vector_store


# ------------------------------------------------------------------ #
#  PROCESSOR                                                           #
# ------------------------------------------------------------------ #

def get_processor():
    """
    Initializes SmartPDFProcessor with available API keys.
    Groq is optional — only needed for enrichment.
    """
    return SmartPDFProcessor(
        gemini_api_key=GEMINI_API_KEY,
        groq_api_key=GROQ_API_KEY,
    )


# ------------------------------------------------------------------ #
#  INGESTION                                                           #
# ------------------------------------------------------------------ #

def prepare_chunks_for_embedding(chunks):
    prepared = []

    for chunk in chunks:
        meta = chunk.metadata

        # LLM description first, regex fallback
        eq_desc = meta.get("equation_description", "")
        if not eq_desc and meta.get("contains_equation"):
            eq_desc = _equation_extractor.augment_for_embedding(
                chunk.page_content,
                section_title=meta.get("section_title", ""),
            )

        section = meta.get("section_title", "")
        topic = meta.get("topic", "")
        summary = meta.get("summary", "")

        parts = []
        if section:
            parts.append(f"Section: {section}")
      
        if eq_desc:
            parts.append(f"Equation: {eq_desc}")

        if parts:
            header = "\n".join(parts)
            chunk.page_content = f"{header}\n\n{chunk.page_content}"

        prepared.append(chunk)

    return prepared

def ingest_pdf(
    pdf_path: str,
    processor: SmartPDFProcessor,
    vector_store: Chroma,
    tier: str = "fast",
    enrich: bool = False,
):
    """
    Processes a single PDF and adds chunks to ChromaDB.

    Args:
        pdf_path:      path to the PDF file
        processor:     SmartPDFProcessor instance
        vector_store:  ChromaDB vector store
        tier:          "fast" or "rich"
        enrich:        whether to run LLM metadata enrichment (needs Groq key)
    """
    pdf_path = str(pdf_path)
    filename = Path(pdf_path).name
    logger.info(f"\n{'='*60}")
    logger.info(f"Ingesting: {filename} (tier={tier}, enrich={enrich})")

    start = time.time()

    # Step 1 — Process PDF
    if tier == "fast":
        chunks = processor.process_pdf_fast(pdf_path)
    else:
        chunks = processor.process_pdf_rich(pdf_path)

    if not chunks:
        logger.warning(f"No chunks produced for {filename} — skipping")
        return 0

    logger.info(f"Produced {len(chunks)} chunks in {time.time() - start:.1f}s")

    # Step 2 — Optional enrichment
    if enrich:
        logger.info("Enriching with semantic metadata...")
        enrich_start = time.time()
        try:
            chunks = enrich_chunks(chunks, processor.groq_client, show_progress=True)
            logger.info(f"Enrichment done in {time.time() - enrich_start:.1f}s")
        except Exception as e:
            logger.error(f"Enrichment failed: {e}")
            logger.warning(
                "Rich-tier embedding skipped. Existing fast-tier chunks can still be used. "
                "User can retry enrichment later."
            )
            return 0
    
    # Step 4 — Deduplicate (delete existing chunks for same document)
    source = chunks[0].metadata.get("source", "")
    document_id = chunks[0].metadata.get("document_id", "")
    if source:
        try:
            existing = vector_store.get(where={"source": source})
            if existing and existing["ids"]:
                    logger.info(f"Found {len(existing['ids'])} existing chunks — replacing")
                    vector_store.delete(ids=existing["ids"])
        except Exception as e:
            logger.warning(f"Dedup check failed: {e} — proceeding with insert")

    # Step 5 — Embed and store
    embed_start = time.time()
    chunks = prepare_chunks_for_embedding(chunks)
    vector_store.add_documents(chunks)
    logger.info(f"Embedded and stored {len(chunks)} chunks in {time.time() - embed_start:.1f}s")

    # Summary
    total_time = time.time() - start
    logger.info(f"Done: {filename} — {len(chunks)} chunks in {total_time:.1f}s")
    _print_sample(chunks[0])

    return {
        "document_id": document_id,
        "filename": filename,
        "chunk_count": len(chunks),
        "tier": tier,
        "status": "embedded",
    }



def ingest_folder(
    folder_path: str,
    processor: SmartPDFProcessor,
    vector_store: Chroma,
    tier: str = "fast",
    enrich: bool = False,
):
    folder = Path(folder_path)
    pdf_files = sorted(folder.glob("*.pdf"))

    if not pdf_files:
        logger.warning(f"No PDFs found in {folder_path}")
        return

    logger.info(f"Found {len(pdf_files)} PDFs in {folder_path}")

    total_chunks = 0
    for pdf_file in pdf_files:
        try:
            result = ingest_pdf(
                pdf_path=str(pdf_file),
                processor=processor,
                vector_store=vector_store,
                tier=tier,
                enrich=enrich,
            )
            if result:
                total_chunks += result.get("chunk_count", 0)
        except Exception as e:
            logger.error(f"Failed to ingest {pdf_file.name}: {e}")
            continue

    logger.info(f"{'='*60}")
    logger.info(f"Done — {total_chunks} chunks from {len(pdf_files)} PDFs")





# ------------------------------------------------------------------ #
#  HELPERS                                                             #
# ------------------------------------------------------------------ #

def _print_sample(chunk):
    """Prints sample metadata from a chunk."""
    m = chunk.metadata
    logger.info(f"  document_id:   {m.get('document_id', '')}")
    logger.info(f"  document_type: {m.get('document_type', '')}")
    logger.info(f"  tier:          {m.get('tier', '')}")
    logger.info(f"  author:        {m.get('author', '')}")
    logger.info(f"  title:         {m.get('title', '')}")
    logger.info(f"  section_title: {m.get('section_title', '')}")


# ------------------------------------------------------------------ #
#  CLI ENTRY POINT                                                     #
# ------------------------------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(description="PDF Ingestion Pipeline")
    parser.add_argument("--pdf", type=str, help="Path to a single PDF")
    parser.add_argument("--folder", type=str, help="Path to a folder of PDFs")
    parser.add_argument("--tier", type=str, default="fast", choices=["fast", "rich"])
    parser.add_argument("--enrich", action="store_true", help="Run LLM metadata enrichment")
    parser.add_argument("--query", type=str, help="Quick test query after ingestion")
    parser.add_argument("--local", action="store_true", help=argparse.SUPPRESS)  # removed: local SQLite no longer supported
    args = parser.parse_args()

    if not args.pdf and not args.folder and not args.query:
        parser.error("Provide --pdf, --folder, or --query")

    # Initialize
    embeddings = get_embedding_model()
    vector_store = get_vector_store(embeddings)
    processor = get_processor()

    # Ingest
    if args.pdf:
        ingest_pdf(args.pdf, processor, vector_store, args.tier, args.enrich)
    elif args.folder:
        ingest_folder(args.folder, processor, vector_store, args.tier, args.enrich)

   


if __name__ == "__main__":
    main()