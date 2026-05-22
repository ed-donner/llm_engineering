"""
enrichment.py — LLM-based metadata enrichment for RAG chunks.

Uses Groq to generate section_title, topic, and summary for each chunk.
Designed to be called after chunking, before embedding.

Usage:
    from groq import Groq
    from .enrichment import enrich

    client = Groq(api_key="...")
    enriched_chunks = enrich(chunks, client)
"""

import re
import time
import logging
from typing import List

from groq import Groq
from pydantic import BaseModel
from langchain_core.documents import Document
from concurrent.futures import ThreadPoolExecutor, as_completed
from .equation_extractor import EquationExtractor

equation_extractor = EquationExtractor()
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# CONFIG
# ------------------------------------------------------------------ #

LLM_MODEL = "llama-3.1-8b-instant"
CHUNKS_PER_BATCH = 4
MAX_WORKERS = 3
SYSTEM_PROMPT = """You generate metadata for RAG document chunks. Return valid JSON only.

For each chunk return:
- chunk_index: integer (must match input)
- section_title: string
- topic: string
- summary: string (1-2 sentences)
- equation_description: string (if equations exist, rewrite them in clean notation AND describe what they compute in plain English. If no equations, return "none")
- equation_rewrites: array of objects with "original" and "clean" keys. For each garbled equation in the chunk, provide the original garbled text and a clean rewrite. Empty array if no equations.

Example:
{"chunks": [{"chunk_index": 0, "section_title": "Attention", "topic": "Scaled dot-product attention", "summary": "Defines the attention function.", "equation_description": "Attention(Q,K,V) = softmax(QK^T / sqrt(d_k))V — computes attention as softmax of scaled dot products multiplied by values.", "equation_rewrites": [{"original": "_Wi[Q] ∈_ R _[d]_[model] _[×][d][k]_", "clean": "W_i^Q ∈ R^{d_model × d_k}"}]}]}"""

# ------------------------------------------------------------------ #
# MODELS
# ------------------------------------------------------------------ #
SKIP_ENRICHMENT_SECTIONS = {
        "References",
        "Bibliography",
        "Preamble",
        "Acknowledgements",
        "Acknowledgments"
    }
class EquationRewrite(BaseModel):
    original: str = ""
    clean: str = ""

class ChunkMetadata(BaseModel):
    chunk_index: int
    section_title: str =""
    topic: str=""
    summary: str=""
    equation_description: str=""
    equation_rewrites: list[EquationRewrite] = []



class EnrichmentResponse(BaseModel):
    chunks: List[ChunkMetadata]


# ------------------------------------------------------------------ #
# PUBLIC API
# ------------------------------------------------------------------ #
def enrich(
    chunks: List[Document],
    client: Groq,
    show_progress: bool = False,
) -> List[Document]:

    if not chunks:
        return chunks

    chunks_to_enrich = [
        chunk for chunk in chunks
        if chunk.metadata.get("section_title") not in SKIP_ENRICHMENT_SECTIONS
    ]

    if not chunks_to_enrich:
        logger.info("No chunks require enrichment")
        return chunks

    batches = _group_into_batches(chunks_to_enrich)
    logger.info(f"Enriching {len(batches)} batch(es)")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_batch = {
            executor.submit(_enrich_batch, batch, client): batch
            for batch in batches
        }

        iterator = as_completed(future_to_batch)

        if show_progress:
            from tqdm.auto import tqdm
            iterator = tqdm(iterator, total=len(batches), desc="Enriching")

        for future in iterator:
            batch = future_to_batch[future]

            try:
                enriched = future.result()
                _apply_enrichment(batch, enriched)

            except Exception as e:
                logger.error(f"Batch enrichment failed: {e}")
                raise RuntimeError(
                    "Rich-tier enrichment failed. "
                    "Do not embed rich chunks. "
                    "Fallback to fast-tier chunks instead."
                ) from e


    logger.info(f"Enrichment done — {len(chunks_to_enrich)} enriched, {len(chunks)} total")
    return chunks


# ------------------------------------------------------------------ #
# INTERNALS
# ------------------------------------------------------------------ #

def _group_into_batches(chunks: List[Document]) -> List[List[Document]]:
    return [
        chunks[i : i + CHUNKS_PER_BATCH]
        for i in range(0, len(chunks), CHUNKS_PER_BATCH)
    ]


def _enrich_batch(batch: List[Document], client: Groq) -> EnrichmentResponse:
    prompt = "Generate metadata for the following chunks:\n\n"

    for chunk in batch:
        idx = chunk.metadata["chunk_index"]

        preview = chunk.page_content[:500]

        section_title = chunk.metadata.get("section_title", "")
        contains_equation = chunk.metadata.get("contains_equation", False)

        equation_preview = ""

        if contains_equation:
            equations = equation_extractor.extract_equation_lines(
                chunk.page_content
            )

            equation_preview = "\n".join(equations[:5])[:300]

        prompt += f"""
    --- Chunk index {idx} ---
    Existing section title: {section_title}
    Contains equation: {contains_equation}

    Detected equations:
    {equation_preview}

    Text:
    {preview}

    """

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content
            raw = re.sub(
                r"^```json\s*|^```\s*|```$",
                "",
                raw,
                flags=re.MULTILINE,
            ).strip()

            return EnrichmentResponse.model_validate_json(raw)

        except Exception as e:
            if "429" in str(e) or "503" in str(e):
                wait_seconds = 15 * (attempt + 1)
                logger.warning(
                    f"Rate limited — retrying in {wait_seconds}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait_seconds)
            else:
                raise

    raise RuntimeError(f"Enrichment failed after {max_retries} retries")


def _apply_enrichment(
    batch: List[Document],
    enriched: EnrichmentResponse,
) -> None:
    enrichment_map = {
        item.chunk_index: item
        for item in enriched.chunks
    }

    for chunk in batch:
        idx = chunk.metadata["chunk_index"]
        meta = enrichment_map.get(idx)

        if not meta:
            raise RuntimeError(f"No enrichment returned for chunk {idx}")

        if not chunk.metadata.get("section_title"):
            chunk.metadata["section_title"] = meta.section_title

        chunk.metadata["topic"] = meta.topic
        chunk.metadata["summary"] = meta.summary
        chunk.metadata["equation_description"] = meta.equation_description
        

        # Replace garbled equations in chunk content
        for rewrite in meta.equation_rewrites:
            if len(rewrite.original) < 5:
                continue
            if rewrite.original in chunk.page_content:
                chunk.page_content = chunk.page_content.replace(
                    rewrite.original, rewrite.clean
                )
            else:
                logger.warning(
                    f"Chunk {idx}: rewrite not found: '{rewrite.original[:50]}'"
                )