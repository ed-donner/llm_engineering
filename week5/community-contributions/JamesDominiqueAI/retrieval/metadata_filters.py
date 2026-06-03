"""
retrieval/metadata_filters.py — Extracts structured filters from natural language questions.
These filters are passed directly to ChromaDB's `where` clause to narrow retrieval.

FIX LOG:
- Removed year from ChromaDB `conditions`: metadata never stores `year`, so adding it
  as a where-clause returned 0 results for ANY question containing a year (2021, 2022, 2023).
  Year is kept as a soft hint for logging/future use only.
- Fixed `doc_type` → `type` to match the key stored by the chunker.
"""

import re
from typing import Dict, Any, Optional


def extract_filters(question: str) -> Dict[str, Any]:
    """
    Parse a user question and return a ChromaDB-compatible `where` filter dict.

    Detects:
    - Year references (e.g. "in 2023", "2021 regulation") — kept as metadata hint only,
      NOT used in ChromaDB where clause (metadata has no 'year' field).
    - Regulation ID references (e.g. "Regulation ABC-2023", "REG-XYZ") — post-filter only.
    - Document type hints (amendment, guidance, audit) — uses 'type' key (matches chunker).

    Returns:
        Dict that can be passed directly to chromadb collection.query(where=...)
        Returns {} if no filters detected (meaning: retrieve from all docs).
    """
    filters = {}
    conditions = []

    # ── Year detection ──────────────────────────────────────────────────────────
    # NOTE: Year is NOT added to ChromaDB conditions because the chunker does not
    # store a 'year' field in metadata. Adding it would return zero results.
    # It is kept as a soft hint for logging and future use.
    year_match = re.search(r"\b(20\d{2})\b", question)
    if year_match:
        filters["year"] = int(year_match.group(1))

    # ── Regulation ID detection ────────────────────────────────────────────────
    # Matches patterns like: REG-ABC-2021, ABC-2023, regulation ABC, REG XYZ
    reg_match = re.search(
        r"(?:regulation\s+|reg[- ]?)([A-Z]{2,5}[-_ ]?(?:20\d{2})?)",
        question,
        re.IGNORECASE,
    )
    if reg_match:
        raw_id = reg_match.group(1).upper().replace(" ", "-").replace("_", "-")
        # Partial match: check if source path contains this string (post-filter in base_retrieval.py)
        filters["_reg_hint"] = raw_id

    # ── Document type detection ────────────────────────────────────────────────
    # Uses 'type' key to match what the chunker stores in metadata (not 'doc_type').
    q_lower = question.lower()
    if any(w in q_lower for w in ["amendment", "amended", "change to"]):
        conditions.append({"type": {"$eq": "amendments"}})
    elif any(w in q_lower for w in ["guidance", "guidance note", "ffca guidance"]):
        conditions.append({"type": {"$eq": "guidance"}})
    elif any(w in q_lower for w in ["audit", "audit report", "compliance report"]):
        conditions.append({"type": {"$eq": "audit_reports"}})

    # ── Build final ChromaDB where clause ─────────────────────────────────────
    # ChromaDB requires $and for multiple conditions
    chroma_where = {}
    if len(conditions) == 1:
        chroma_where = conditions[0]
    elif len(conditions) > 1:
        chroma_where = {"$and": conditions}

    return {
        "chroma_where": chroma_where,          # Pass directly to ChromaDB
        "reg_hint": filters.get("_reg_hint"),  # Used for post-filter in retrieval
        "year": filters.get("year"),           # Convenience accessor (logging only)
    }


def describe_filters(filters: dict) -> str:
    """Human-readable description of applied filters (for logging/UI)."""
    parts = []
    if filters.get("year"):
        parts.append(f"year≈{filters['year']} (hint only)")
    if filters.get("reg_hint"):
        parts.append(f"regulation≈'{filters['reg_hint']}'")
    if filters.get("chroma_where"):
        doc_type = filters["chroma_where"].get("type", {}).get("$eq")
        if doc_type:
            parts.append(f"type={doc_type}")
    return ", ".join(parts) if parts else "none"


if __name__ == "__main__":
    test_questions = [
        "What changed in the 2023 regulation?",
        "What are the breach notification rules in REG-ABC-2021?",
        "Show me amendments to regulation ABC",
        "What did the 2022 audit report say about encryption?",
        "What is the penalty for unauthorized data sharing?",
        "Tell me about FFCA guidance on cloud storage in 2023",
    ]
    for q in test_questions:
        f = extract_filters(q)
        print(f"Q: {q}")
        print(f"   Filters: {describe_filters(f)}")
        print(f"   Raw: {f}\n")
