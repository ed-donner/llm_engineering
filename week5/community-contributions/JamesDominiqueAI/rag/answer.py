#answer.py
"""
rag/answer.py — Answer generation using litellm (supports OpenAI, Groq, Anthropic, etc.)

Full pipeline:
  1. Rewrite the query (LLM)
  2. Dual retrieval on original + rewritten query
  3. LLM rerank
  4. Generate answer with context + history
  5. Return answer + confidence + sources
"""

import os
import sys
from typing import List, Dict, Any, Tuple
from tenacity import retry, wait_exponential
from litellm import completion

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL, RETRY_MIN_WAIT, RETRY_MAX_WAIT
from rag.rewrite import rewrite_query
from retrieval.base_retrieval import Result, fetch_context_unranked, merge_chunks, rerank

wait = wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT)

SYSTEM_PROMPT = """
You are a knowledgeable regulatory compliance expert assistant.
You answer questions strictly based on the provided regulatory document extracts.

Follow these rules on every response:
1. ACCURACY — Only state facts that are explicitly in the extracts. Never invent figures, dates, IDs, or rules.
   If a specific value is not present, say so clearly rather than guessing.
2. COMPLETENESS — Cover EVERY relevant detail from the extracts: regulation IDs, section numbers,
   exact deadlines, exact dollar amounts, percentages, named requirements, and conditions.
   Do not summarise away specific values — include them all.
3. COMPARISONS — When asked what changed between two periods, explicitly state the old value AND
   the new value side by side (e.g. "changed from 72 hours (REG-ABC-2021) to 48 hours (REG-ABC-2023)").
4. CITATIONS — Cite the regulation ID and section number for every fact you state.
5. HONESTY — If the extracts do not contain enough information to fully answer, clearly state
   what is and is not available rather than filling in gaps.

For context, here are specific extracts from the Knowledge Base:
{context}

With this context, please answer the user's question following all five rules above.
"""


def _build_context(chunks: List[Result]) -> str:
    """Format retrieved chunks into a readable context block with source labels."""
    parts = []
    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        doc_type = chunk.metadata.get("type", "")
        parts.append(f"Extract from {source} ({doc_type}):\n{chunk.page_content}")
    return "\n\n".join(parts)


def _make_rag_messages(question: str, history: List[Dict], chunks: List[Result]) -> List[Dict]:
    """Build the full message list: system prompt with context + history + current question."""
    context = _build_context(chunks)
    system_prompt = SYSTEM_PROMPT.format(context=context)
    return (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": question}]
    )


@retry(wait=wait)
def answer_question(
    question: str,
    history: List[Dict] = [],
) -> Tuple[str, List[Result]]:
    """
    Full RAG pipeline: rewrite → dual retrieve → rerank → answer.
    """
    # Step 1: Single rewrite call
    rewritten = rewrite_query(question, history)
    print(f"[Answer] Rewritten query: {rewritten}")

    # Step 2: Dual retrieval using original + rewritten (no further rewrites)
    chunks1 = fetch_context_unranked(question)
    chunks2 = fetch_context_unranked(rewritten) if rewritten != question else []
    merged = merge_chunks(chunks1, chunks2)
    chunks = rerank(question, merged)
    print(f"[Answer] Retrieved {len(chunks)} chunks after rerank")

    # Step 3: Generate answer
    messages = _make_rag_messages(question, history, chunks)
    response = completion(model=MODEL, messages=messages)
    answer = response.choices[0].message.content.strip()

    return answer, chunks


def format_answer_package(
    answer: str,
    chunks: List[Result],
    confidence: float,
) -> Dict[str, Any]:
    """
    Package the answer with confidence score and source citations for the UI.
    """
    if confidence >= 0.75:
        confidence_label, confidence_color = "HIGH", "green"
    elif confidence >= 0.5:
        confidence_label, confidence_color = "MEDIUM", "yellow"
    else:
        confidence_label, confidence_color = "LOW", "red"

    sources = []
    seen = set()
    for chunk in chunks:
        src = chunk.metadata.get("source", "")
        if src and src not in seen:
            seen.add(src)
            sources.append({
                "source": src,
                "type": chunk.metadata.get("type", ""),
                "score": getattr(chunk, "score", 0),
            })

    return {
        "answer": answer,
        "confidence": round(confidence, 3),
        "confidence_label": confidence_label,
        "confidence_color": confidence_color,
        "sources": sources,
        "num_chunks_used": len(chunks),
    }