import tempfile
import logging
from typing import List
from google import genai
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from groq import Groq
from .enrichment import enrich
from .text_extractor import TextExtractor
from .table_extractor import TableExtractor
from .image_captioner import ImageCaptioner
from .chunker import Chunker
from .metadata import build_metadata, build_fast_metadata
import pymupdf

logger = logging.getLogger(__name__)


class SmartPDFProcessor:
    """
    Two-tier PDF processor for RAG ingestion.

    Tier 1 — process_pdf_fast():
        PyPDFLoader + pdfplumber tables + structure-aware chunking.
        No LLM calls. Instant. Queryable immediately.

    Tier 2 — process_pdf_rich():
        pymupdf4llm + pdfplumber tables + Gemini image captioning
        + structure-aware chunking + Groq semantic enrichment.
        Runs in background. Replaces Tier 1 chunks.

    pdfplumber used in BOTH tiers — better table extraction than
    either PyPDFLoader or pymupdf4llm alone.

    Args:
        gemini_api_key  : Gemini API key (image captioning)
        groq_api_key    : Groq API key (optional, semantic enrichment)
        gemini_model    : Gemini model for image captioning
        max_workers     : Gemini batch parallelism
        document_type   : fallback if auto-detection returns unknown
    """

    def __init__(
        self,
        gemini_api_key: str,
        groq_api_key: str = "",
        gemini_model: str = "gemini-2.5-flash-lite",
        max_workers: int = 1,
        document_type: str = "book",
    ):
        gemini_client = genai.Client(api_key=gemini_api_key)

        self.document_type   = document_type
        self.text_extractor  = TextExtractor()
        self.table_extractor = TableExtractor()
        self.image_captioner = ImageCaptioner(gemini_client, gemini_model, max_workers)
        self.chunker = Chunker()
        self.groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

    # ------------------------------------------------------------------ #
    #  TIER 1 — FAST (no LLM)                                             #
    # ------------------------------------------------------------------ #

    def process_pdf_fast(self, pdf_path: str) -> List[Document]:
        """
        Tier 1 — fast ingestion.
        PyPDFLoader + pdfplumber tables + structure-aware chunking.
        No LLM calls. Instant. Queryable immediately.
        """
        pdf_path = str(pdf_path)
        logger.info(f"Fast ingestion: {pdf_path}")

        try:
            # Step 1 — load pages
            pages = PyPDFLoader(pdf_path).load()
            first_page_meta = pages[0].metadata if pages else {}

            # Step 2 — join pages with markers
            full_text = ""
            for page in pages:
                page_num = page.metadata.get("page", 0) + 1
                full_text += f"\n\n[Page {page_num}]\n{page.page_content}"

            # Step 3 — extract tables via pdfplumber and inject inline
            tables_by_page = self.table_extractor.extract(pdf_path)
            full_text = self._inject_tables(full_text, tables_by_page)

            # Step 4 — build metadata
            metadata = build_metadata(
                pdf_path=pdf_path,
                document_type=self.document_type,
                author=first_page_meta.get("author", ""),
                title=first_page_meta.get("title", ""),
                tier = "fast"
            )

            # Step 5 — structure-aware chunking
            chunks = self.chunker.chunk_fast(
                text=full_text,
                metadata=metadata,
            )

            # Step 6 — auto-detect document_type
            self._auto_detect_type(chunks, full_text)

            logger.info(f"Fast done — {len(chunks)} chunks from {pdf_path}")
            return chunks

        except Exception as e:
            logger.error(f"Fast ingestion failed for {pdf_path}: {e}")
            return []

    # ------------------------------------------------------------------ #
    #  TIER 2 — RICH (with image captioning + LLM enrichment)             #
    # ------------------------------------------------------------------ #

    def process_pdf_rich(self, pdf_path: str) -> List[Document]:
        pdf_path = str(pdf_path)
        logger.info(f"Rich ingestion: {pdf_path}")

        try:
            with tempfile.TemporaryDirectory() as img_dir:
                md_pages = self.text_extractor.extract(pdf_path, img_dir)
                tables_by_page = self.table_extractor.extract(pdf_path)
                images_by_page = self.image_captioner.collect(img_dir)
                captions_by_page = self.image_captioner.caption(images_by_page)

            full_text = self._build_full_text(
                md_pages, tables_by_page, captions_by_page
            )

            if len(full_text.strip()) < 100:
                logger.warning(f"Extracted text too short for {pdf_path}")
                return []

           
            pdf_meta = pymupdf.open(pdf_path).metadata or {}

            metadata = build_metadata(
                pdf_path=pdf_path,
                tier="rich",
                author=pdf_meta.get("author", ""),
                title=pdf_meta.get("title", ""),
                document_type=self.document_type,
            )

            chunks = self.chunker.chunk_fast(
                text=full_text,
                metadata=metadata,
            )

            self._auto_detect_type(chunks, full_text)

            # Enrichment (optional)
            if self.groq_client:
                chunks = enrich(chunks, self.groq_client)

            logger.info(f"Rich done — {len(chunks)} chunks from {pdf_path}")
            return chunks

        except Exception as e:
            logger.exception(f"Rich ingestion failed for {pdf_path}")
            raise
    # ------------------------------------------------------------------ #
    #  INSPECTION                                                           #
    # ------------------------------------------------------------------ #

    def inspect_extraction(self, pdf_path: str) -> dict:
        """
        Runs extraction pipeline minus chunking.
        Use in a notebook to verify text, tables, and captions.
        """
        pdf_path = str(pdf_path)

        with tempfile.TemporaryDirectory() as img_dir:
            md_pages = self.text_extractor.extract(pdf_path, img_dir)
            tables_by_page = self.table_extractor.extract(pdf_path)
            images_by_page = self.image_captioner.collect(img_dir)
            captions_by_page = self.image_captioner.caption(images_by_page)

        return {
            "total_pages": len(md_pages),
            "pages": [
                {
                    "page": i + 1,
                    "text_preview": self.text_extractor.clean(page["text"])[:300],
                    "tables": tables_by_page.get(i + 1, []),
                    "captions": captions_by_page.get(i + 1, []),
                }
                for i, page in enumerate(md_pages)
            ],
        }

    # ------------------------------------------------------------------ #
    #  INTERNAL                                                             #
    # ------------------------------------------------------------------ #

    def _inject_tables(self, full_text: str, tables_by_page: dict) -> str:
        """
        Injects pdfplumber tables inline at their [Page N] marker.
        Used by fast tier where PyPDFLoader doesn't extract tables well.
        """
        if not tables_by_page:
            return full_text

        logger.info(f"Injecting tables from {len(tables_by_page)} pages")
        for page_num, tables in tables_by_page.items():
            marker = f"[Page {page_num}]"
            table_text = "\n\n".join(tables)
            full_text = full_text.replace(
                marker,
                f"{marker}\n\n{table_text}",
                1,
            )

        return full_text

    def _build_full_text(
        self,
        md_pages: list,
        tables_by_page: dict,
        captions_by_page: dict,
    ) -> str:
        """
        Concatenates all pages into one enriched document string.
        [Page N] markers injected for page range tracking.
        pdfplumber tables and image captions injected inline.
        """
        sections = []

        for i, page_data in enumerate(md_pages):
            page_num = i + 1
            page_text = self.text_extractor.clean(page_data["text"])
            sections.append(f"\n\n[Page {page_num}]\n{page_text}")

            # pdfplumber tables — better quality than pymupdf4llm
            for table in tables_by_page.get(page_num, []):
                sections.append(f"\n\n{table}")

            # Image captions from Gemini
            for cap in captions_by_page.get(page_num, []):
                if cap.get("type") == "logo":
                    continue
                line = f"\n\n[{cap['type'].upper()}] {cap['caption']}"
                if cap.get("key_data"):
                    line += f" Key data: {cap['key_data']}"
                sections.append(line)

        return "".join(sections)

    def _auto_detect_type(self, chunks: List[Document], full_text: str):
        """
        Overrides document_type in chunk metadata if structure
        detector identifies the document type with confidence.
        """
        detected = self.chunker.detector.detect(full_text)
        if detected["document_type"] != "unknown":
            for chunk in chunks:
                chunk.metadata["document_type"] = detected["document_type"]