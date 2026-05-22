"""
chunker.py — Chunking logic for RAG ingestion.

Detects document structure and splits text into chunks
with metadata ready for embedding.

Delegates to:
- cleaners.py for text cleaning
- table_extractor.py for broken table detection
- equation_extractor.py for equation detection
- enrichment.py for LLM metadata enrichment (called externally)
"""

import re
import logging
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .structure_detector import StructureDetector
from .cleaners import clean_chunk_text
from .table_extractor import looks_like_broken_table
from .equation_extractor import EquationExtractor

logger = logging.getLogger(__name__)

_equation_extractor = EquationExtractor()


class Chunker:
    MAX_SECTION_SIZE = 3000

    def __init__(
        self,
        chunk_size: int = 900,
        chunk_overlap: int = 120,
    ):
        self.detector = StructureDetector()

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk_fast(self, text: str, metadata: dict) -> List[Document]:
        if len(text.strip()) < 100:
            logger.warning("Text too short to chunk — skipping")
            return []

        structure = self.detector.detect(text)
        strategy = structure["recommended_strategy"]

        logger.info(
            f"Detected: {structure['document_type']} — using {strategy} strategy"
        )

        if strategy == "section":
            chunks = self._chunk_by_sections(text, metadata)
        elif strategy == "header":
            chunks = self._chunk_by_headers(text, metadata)
        else:
            chunks = self._chunk_by_text_splitter(text, metadata)

        logger.info(f"Fast chunking done — {len(chunks)} chunks via {strategy}")

        cleaned_chunks = []

        for chunk in chunks:
            chunk.page_content = clean_chunk_text(chunk.page_content)

            if looks_like_broken_table(chunk.page_content):
                continue

            if len(chunk.page_content.strip()) < 80:
                continue

            chunk.metadata["contains_equation"] = (
                _equation_extractor.contains_equation(chunk.page_content)
            )
            chunk.metadata["equation_description"] = ""

            cleaned_chunks.append(chunk)

        for i, chunk in enumerate(cleaned_chunks):
            chunk.metadata["chunk_index"] = i

        return cleaned_chunks

    # ------------------------------------------------------------------ #
    # CHUNKING STRATEGIES
    # ------------------------------------------------------------------ #

    def _chunk_by_sections(self, text: str, metadata: dict) -> List[Document]:
        sections = self.detector.split_by_sections(text)
        return self._chunk_from_sections(sections, metadata)

    def _chunk_by_headers(self, text: str, metadata: dict) -> List[Document]:
        sections = self.detector.split_by_headers(text)
        return self._chunk_from_sections(sections, metadata)

    def _chunk_from_sections(self, sections: list, metadata: dict) -> List[Document]:
        chunks = []

        for section in sections:
            content = section["content"]

            section_meta = {
                **metadata,
                "section_title": section["section_title"],
                "page_start": section["page_start"],
                "page_end": section["page_end"],
                "topic": "",
                "summary": "",
            }

            if len(content) > self.MAX_SECTION_SIZE:
                sub_chunks = self.text_splitter.create_documents(
                    texts=[content],
                    metadatas=[section_meta],
                )

                for sub_chunk in sub_chunks:
                    sub_chunk.metadata["chunk_index"] = len(chunks)

                    page_start, page_end = self._extract_page_range(
                        sub_chunk.page_content
                    )

                    if page_start != 0:
                        sub_chunk.metadata["page_start"] = page_start
                        sub_chunk.metadata["page_end"] = page_end

                    chunks.append(sub_chunk)

            else:
                section_meta["chunk_index"] = len(chunks)
                chunks.append(
                    Document(
                        page_content=content,
                        metadata=section_meta,
                    )
                )

        return chunks

    def _chunk_by_text_splitter(self, text: str, metadata: dict) -> List[Document]:
        raw_chunks = self.text_splitter.create_documents(
            texts=[text],
            metadatas=[metadata],
        )

        for i, chunk in enumerate(raw_chunks):
            page_start, page_end = self._extract_page_range(chunk.page_content)

            chunk.metadata["chunk_index"] = i
            chunk.metadata["page_start"] = page_start
            chunk.metadata["page_end"] = page_end
            chunk.metadata["section_title"] = ""
            chunk.metadata["topic"] = ""
            chunk.metadata["summary"] = ""

        return raw_chunks

    # ------------------------------------------------------------------ #
    # HELPERS
    # ------------------------------------------------------------------ #

    def _extract_page_range(self, content: str) -> tuple[int, int]:
        markers = re.findall(r"\[Page (\d+)\]", content)

        if not markers:
            return (0, 0)

        pages = [int(marker) for marker in markers]
        return (min(pages), max(pages))