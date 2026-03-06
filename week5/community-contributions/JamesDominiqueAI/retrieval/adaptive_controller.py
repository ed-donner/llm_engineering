"""
retrieval/adaptive_controller.py — Adaptive Self-Tuning Retrieval Controller.

Runs retrieval in a loop, scoring quality at each attempt.
Widens k and rewrites the query if confidence is low.
Uses dual retrieval + LLM reranker from base_retrieval.
"""

import os
import sys
import re
from typing import List, Dict, Any, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DEFAULT_K, MAX_K, ADAPTIVE_MAX_ATTEMPTS,
    CONFIDENCE_THRESHOLD, MIN_CONFIDENCE_FOR_REWRITE,
)
from retrieval.base_retrieval import fetch_context_unranked, rerank, merge_chunks, Result, retrieve
from retrieval.metadata_filters import extract_filters
from rag.rewrite import rewrite_query


# ── Confidence Scoring ─────────────────────────────────────────────────────────

def compute_keyword_overlap(question: str, chunks: List[Result]) -> float:
    stopwords = {
        "what", "when", "where", "who", "how", "is", "are", "was", "were",
        "the", "a", "an", "in", "on", "of", "to", "for", "and", "or", "with",
        "did", "do", "does", "has", "have", "had", "be", "been", "being",
        "this", "that", "these", "those", "from", "by", "at", "as", "into",
        "about", "tell", "me", "us", "show", "list", "give", "any", "all",
    }
    words = set(re.findall(r"\b[a-zA-Z]{3,}\b", question.lower()))
    keywords = words - stopwords
    if not keywords or not chunks:
        return 0.0
    combined = " ".join(c.page_content.lower() for c in chunks)
    matched = sum(1 for kw in keywords if kw in combined)
    return min(1.0, matched / len(keywords))


def average_embedding_similarity(chunks: List[Result]) -> float:
    if not chunks:
        return 0.0
    top_scores = sorted([getattr(c, "score", 0) for c in chunks], reverse=True)[:5]
    return sum(top_scores) / len(top_scores)


def retrieval_confidence_score(chunks: List[Result], question: str) -> float:
    """60% keyword overlap + 40% average semantic similarity."""
    if not chunks:
        return 0.0
    kw = compute_keyword_overlap(question, chunks)
    sem = average_embedding_similarity(chunks)
    return round(0.6 * kw + 0.4 * sem, 4)


# ── Adaptive Controller ────────────────────────────────────────────────────────

def adaptive_retrieve(
    question: str,
    history: List[Dict] = [],
    max_attempts: int = ADAPTIVE_MAX_ATTEMPTS,
) -> Tuple[List[Result], float, Dict]:
    """
    Adaptive retrieval loop with dual retrieval and LLM reranking.

    1. Rewrite query
    2. Dual retrieve (original + rewritten)
    3. LLM rerank
    4. Score confidence
    5. If below threshold: widen k, re-retrieve
    6. Return best result

    Returns:
        chunks:  Final list of Result objects
        score:   Confidence score (0–1)
        trace:   Debug info dict
    """
    current_question = question
    rewritten = rewrite_query(question, history)
    k = DEFAULT_K
    best_chunks: List[Result] = []
    best_score = 0.0

    trace = {
        "original_question": question,
        "rewritten_question": rewritten,
        "attempts": [],
        "rewrites": [],
    }

    for attempt in range(1, max_attempts + 1):
        print(f"[Adaptive] Attempt {attempt}/{max_attempts} | k={k} | Q: '{current_question[:70]}'")

        # Dual retrieval
        chunks1 = fetch_context_unranked(current_question, k=k)
        chunks2 = fetch_context_unranked(rewritten, k=k) if rewritten != current_question else []
        merged = merge_chunks(chunks1, chunks2)
        chunks = rerank(current_question, merged)

        score = retrieval_confidence_score(chunks, current_question)
        print(f"[Adaptive] Confidence: {score:.3f} (threshold: {CONFIDENCE_THRESHOLD})")

        trace["attempts"].append({
            "attempt": attempt,
            "k": k,
            "question_used": current_question,
            "num_chunks": len(chunks),
            "confidence": score,
        })

        if score > best_score:
            best_score = score
            best_chunks = chunks

        if score >= CONFIDENCE_THRESHOLD:
            print(f"[Adaptive] ✅ Threshold met at attempt {attempt}")
            break

        if attempt == max_attempts:
            print(f"[Adaptive] ⚠️  Max attempts reached. Best score: {best_score:.3f}")
            break

        # Low confidence: rewrite again with more context
        if score < MIN_CONFIDENCE_FOR_REWRITE:
            new_q = rewrite_query(
                f"{question} — focus on specific rules, deadlines, penalties, and requirements",
                history,
            )
            if new_q != current_question:
                trace["rewrites"].append({"from": current_question, "to": new_q, "score": score})
                current_question = new_q
                rewritten = new_q

        k = min(k + 10, MAX_K)

    return best_chunks, best_score, trace

