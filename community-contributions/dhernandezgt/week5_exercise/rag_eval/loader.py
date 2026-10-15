"""
Loads the eval CSV and normalizes the `assertions` / `source_keywords`
columns, which may be stored as JSON-list strings, pipe-separated, or
semicolon-separated text depending on how the CSV was authored.
"""
from __future__ import annotations
import ast
import csv
import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any


def _parse_list_field(raw: str) -> List[str]:
    """Handle assertions/keywords stored as JSON array, Python-repr list
    (single-quoted, e.g. from str(list) in pandas/Python), or | / ; / , separated text."""
    if raw is None:
        return []
    raw = raw.strip()
    if not raw:
        return []
    # Try JSON list first: '["fact1", "fact2"]'
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            return [str(x).strip() for x in parsed if str(x).strip()]
        except json.JSONDecodeError:
            pass
        # Python-repr list, e.g. "['fact1', 'fact2']" (single quotes -> invalid JSON)
        try:
            parsed = ast.literal_eval(raw)
            if isinstance(parsed, (list, tuple)):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except (ValueError, SyntaxError):
            pass
    # Fall back to delimiter splitting; prefer '|' or ';' since commas
    # often appear inside the assertion text itself.
    for delim in ["|", ";"]:
        if delim in raw:
            return [p.strip() for p in raw.split(delim) if p.strip()]
    # Last resort: single assertion, or comma-split if it looks like short keywords
    if "," in raw and len(raw) < 200:
        return [p.strip() for p in raw.split(",") if p.strip()]
    return [raw]


@dataclass
class EvalCase:
    id: str
    question: str
    gold_answer: str
    source_doc: str
    source_keywords: List[str] = field(default_factory=list)
    difficulty: str = ""
    question_type: str = ""
    assertions: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


def load_eval_csv(path: str) -> List[EvalCase]:
    cases = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = {"id", "question", "gold_answer", "source_doc",
                   "source_keywords", "difficulty", "question_type", "assertions"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing expected columns: {missing}")
        for row in reader:
            cases.append(EvalCase(
                id=row["id"],
                question=row["question"],
                gold_answer=row["gold_answer"],
                source_doc=row["source_doc"],
                source_keywords=_parse_list_field(row["source_keywords"]),
                difficulty=row["difficulty"],
                question_type=row["question_type"],
                assertions=_parse_list_field(row["assertions"]),
                raw=row,
            ))
    return cases
