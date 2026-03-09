"""
RAG evaluation: MRR (retrieval) and LLM-as-judge (answer quality).
Used by eval_app.py Gradio UI.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from answer import answer_question, fetch_context

# Reuse answer.py LLM for judge
from answer import llm

logging.basicConfig(level=logging.WARNING)


@dataclass
class EvalExample:
    """Single evaluation example: question + optional expected answer/sources."""
    question: str
    expected_sources: list[str] = field(default_factory=list)  # e.g. ["about-galdunx.md"]
    expected_answer: str | None = None  # optional; used for LLM judge


def _doc_source(doc: Document) -> str:
    """Normalize source to filename for matching (e.g. 'knowledge-base/about-galdunx.md' -> 'about-galdunx.md')."""
    raw = (doc.metadata or {}).get("source", "")
    return Path(raw).name if raw else ""


def compute_mrr_one(question: str, retrieved_docs: list[Document], expected_sources: list[str]) -> float:
    """
    MRR for one query: 1/rank of first relevant doc, or 0 if none.
    Relevant = doc source filename (e.g. about-galdunx.md) in expected_sources.
    """
    if not expected_sources:
        return 0.0
    expected_set = {s.strip().lower() for s in expected_sources}
    for rank, doc in enumerate(retrieved_docs, start=1):
        src = _doc_source(doc).lower()
        if any(src == e or src.endswith(e) for e in expected_set):
            return 1.0 / rank
    return 0.0


def compute_mrr(eval_set: list[EvalExample], fetch_context_fn=None) -> tuple[float, list[tuple[EvalExample, list[Document], float]]]:
    """
    Run retrieval (fetch_context) for each example and compute MRR.
    Returns (mean_MRR, list of (example, retrieved_docs, mrr_score)).
    """
    if fetch_context_fn is None:
        fetch_context_fn = lambda q, h: fetch_context(q, h or [])
    results: list[tuple[EvalExample, list[Document], float]] = []
    for ex in eval_set:
        docs = fetch_context_fn(ex.question, [])
        mrr = compute_mrr_one(ex.question, docs, ex.expected_sources)
        results.append((ex, docs, mrr))
    n = len(results)
    mean_mrr = sum(r[2] for r in results) / n if n else 0.0
    return mean_mrr, results


class JudgeResult(BaseModel):
    """LLM judge output for one answer."""
    score: int = Field(description="Score from 1 to 5, where 5 is fully correct and relevant")
    reasoning: str = Field(description="Brief explanation for the score")


def llm_judge_one(question: str, model_answer: str, context_snippet: str, expected_answer: str | None = None) -> JudgeResult:
    """
    Use LLM to judge one RAG answer: relevance, correctness, completeness.
    If expected_answer is provided, judge against it; otherwise judge against context only.
    """
    expected_part = ""
    if expected_answer:
        expected_part = f"\nExpected answer (reference): {expected_answer}\n"
    system_prompt = """You are an evaluator for a RAG (retrieval-augmented generation) system. You will see:
1. The user question
2. The context that was retrieved (excerpt)
3. The model's answer
4. Optionally a reference expected answer

Score the model's answer from 1 to 5:
- 5: Fully correct, relevant, and complete; uses context appropriately.
- 4: Mostly correct and relevant; minor omissions or slight inaccuracies.
- 3: Partially correct; some relevant info but missing key points or some inaccuracy.
- 2: Weak; little relevance or several inaccuracies.
- 1: Wrong, irrelevant, or contradicts context.

Reply with a JSON object with keys "score" (integer 1-5) and "reasoning" (brief explanation)."""
    user_prompt = f"""Question: {question}
{expected_part}
Context excerpt (first 800 chars): {context_snippet[:800]}

Model answer: {model_answer}

Provide your score and reasoning (JSON with "score" and "reasoning")."""
    structured = llm.with_structured_output(JudgeResult)
    out = structured.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    return out


def run_answer_eval(
    eval_set: list[EvalExample],
    answer_fn=None,
) -> tuple[float, list[tuple[EvalExample, str, list[Document], JudgeResult]]]:
    """
    Run full RAG (answer_question) for each example, then LLM judge each answer.
    Returns (mean_judge_score, list of (example, answer, docs, judge_result)).
    """
    if answer_fn is None:
        answer_fn = answer_question
    results: list[tuple[EvalExample, str, list[Document], JudgeResult]] = []
    for ex in eval_set:
        answer, docs = answer_fn(ex.question, [])
        context_snippet = "\n\n".join(d.page_content for d in docs)[:1200]
        judge = llm_judge_one(ex.question, answer, context_snippet, ex.expected_answer)
        results.append((ex, answer, docs, judge))
    n = len(results)
    mean_score = sum(r[3].score for r in results) / n if n else 0.0
    return mean_score, results


def default_eval_set() -> list[EvalExample]:
    """Default eval set for Galdunx knowledge base."""
    return [
        EvalExample(
            question="What is Galdunx and what does it do?",
            expected_sources=["about-galdunx.md"],
            expected_answer="Galdunx is a digital product and creative technology studio that designs and builds digital solutions. It offers web development, UI/UX design, and helps businesses turn ideas into scalable products.",
        ),
        EvalExample(
            question="What web technologies does Galdunx use?",
            expected_sources=["web-development.md"],
            expected_answer="Next.js, React, Node.js, Nest.js, REST APIs, and related web technologies.",
        ),
        EvalExample(
            question="What is the 10K Store?",
            expected_sources=["10k-store.md"],
            expected_answer="An affordable e-commerce solution: ready-to-launch online store with product listing, payments, and mobile-friendly design.",
        ),
        EvalExample(
            question="What UI/UX design services does Galdunx offer?",
            expected_sources=["uiux-design.md"],
            expected_answer="User interfaces for SaaS/dashboards, user experience design, design systems; tools like Figma.",
        ),
        EvalExample(
            question="Which industries does Galdunx serve?",
            expected_sources=["about-galdunx.md"],
            expected_answer="SaaS, blockchain/Web3, fintech, healthcare, and other industries.",
        ),
    ]


def load_eval_set_from_json(path: str | Path) -> list[EvalExample]:
    """Load eval set from JSON: list of {question, expected_sources?, expected_answer?}."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for item in data:
        out.append(EvalExample(
            question=item["question"],
            expected_sources=item.get("expected_sources", []),
            expected_answer=item.get("expected_answer"),
        ))
    return out
