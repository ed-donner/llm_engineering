# answer_eval.py
"""
evaluation/answer_eval.py — End-to-end answer quality evaluation using LLM-as-a-judge.

Scores each answer on:
  - Accuracy (1–5): Is it factually correct vs. the reference answer?
  - Completeness (1–5): Does it cover all aspects of the reference?
  - Relevance (1–5): Does it stay on-topic without adding noise?

Uses litellm (same MODEL as the rest of the system) with structured outputs.
"""

import os
import sys
import json
from typing import Generator, Tuple, List
from pydantic import BaseModel, Field
from tenacity import retry, wait_exponential

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL, EVAL_RESULTS_DIR, RETRY_MIN_WAIT, RETRY_MAX_WAIT
from rag.answer import answer_question
from evaluation.retrieval_eval import TestQuestion, load_tests
from utils.json_completion import json_completion

wait = wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT)


# ── Answer Eval Model ──────────────────────────────────────────────────────────

class AnswerEval(BaseModel):
    feedback: str = Field(
        description="Concise feedback comparing the generated answer to the reference answer"
    )
    accuracy: float = Field(
        description=(
            "Factual correctness vs reference answer. "
            "5=all stated facts correct. 4=correct, minor wording diff. "
            "3=correct on main point, slightly off on detail. "
            "2=partially correct with one factual error. "
            "1=states facts that directly contradict the reference. "
            "If the answer says info is not available and states NO wrong facts, score 3 not 1."
        )
    )
    completeness: float = Field(
        description=(
            "Coverage of all aspects from the reference answer. "
            "5=covers every point. 4=covers all main points, trivial details missing. "
            "3=covers core concept but missing 1-2 specific values. "
            "2=covers only part of the reference. 1=completely misses the question. "
            "Award partial credit — do not score 1 just because specific numbers are absent "
            "if the conceptual answer is correct."
        )
    )
    relevance: float = Field(
        description="How directly the answer addresses the question without extra noise. 1=off-topic, 5=perfectly focused."
    )


# ── LLM Judge ─────────────────────────────────────────────────────────────────

@retry(wait=wait)
def evaluate_answer(test: TestQuestion) -> Tuple[AnswerEval, str, list]:
    """
    Generate an answer with the RAG pipeline, then have the LLM judge it.

    Returns:
        (AnswerEval, generated_answer, retrieved_chunks)
    """
    generated_answer, retrieved_chunks = answer_question(test.question)

    judge_messages = [
        {
            "role": "system",
            "content": (
                "You are a fair and calibrated evaluator of regulatory compliance RAG systems. "
                "Score answers using partial credit — not every answer is either perfect or terrible. "
                "Read the scoring criteria in each field description carefully before scoring."
            ),
        },
        {
            "role": "user",
            "content": f"""Question:
{test.question}

Generated Answer:
{generated_answer}

Reference Answer:
{test.reference_answer}

Evaluate the generated answer on Accuracy, Completeness, and Relevance.
Be fair: award partial credit where deserved. Only score Accuracy=1 if the answer
states facts that directly contradict the reference — not merely for being incomplete.""",
        },
    ]

    return json_completion(MODEL, judge_messages, AnswerEval), generated_answer, retrieved_chunks


def evaluate_all_answers() -> Generator[Tuple[TestQuestion, AnswerEval, float], None, None]:
    """Generator — yields (test, result, progress) for streaming into Gradio."""
    tests = load_tests()
    for i, test in enumerate(tests):
        result = evaluate_answer(test)[0]
        yield test, result, (i + 1) / len(tests)


def run_cli_eval(verbose: bool = True) -> dict:
    """Run full answer eval from CLI."""
    os.makedirs(EVAL_RESULTS_DIR, exist_ok=True)
    tests = load_tests()
    results = []
    total_acc = total_comp = total_rel = 0.0

    print(f"\n{'='*70}\nANSWER EVALUATION — LLM-as-Judge ({len(tests)} tests)\n{'='*70}\n")

    for test in tests:
        eval_result, generated, chunks = evaluate_answer(test)
        total_acc += eval_result.accuracy
        total_comp += eval_result.completeness
        total_rel += eval_result.relevance
        results.append({
            "question": test.question,
            "category": test.category,
            "accuracy": eval_result.accuracy,
            "completeness": eval_result.completeness,
            "relevance": eval_result.relevance,
            "feedback": eval_result.feedback,
            "generated_answer": generated,
            "reference_answer": test.reference_answer,
        })
        if verbose:
            avg = (eval_result.accuracy + eval_result.completeness + eval_result.relevance) / 3
            status = "✅" if avg >= 4.0 else ("⚠️" if avg >= 3.0 else "❌")
            print(f"{status} [{test.category}] {test.question[:60]}")
            print(f"   Accuracy: {eval_result.accuracy}/5  Completeness: {eval_result.completeness}/5  Relevance: {eval_result.relevance}/5")
            print(f"   Feedback: {eval_result.feedback[:120]}\n")

    n = len(tests)
    summary = {
        "avg_accuracy": round(total_acc / n, 2),
        "avg_completeness": round(total_comp / n, 2),
        "avg_relevance": round(total_rel / n, 2),
        "results": results,
    }
    print(f"\n{'='*70}")
    print(f"Avg Accuracy: {summary['avg_accuracy']}/5  |  Avg Completeness: {summary['avg_completeness']}/5  |  Avg Relevance: {summary['avg_relevance']}/5")
    print(f"{'='*70}")

    out = os.path.join(EVAL_RESULTS_DIR, "answer_eval.json")
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved to {out}")
    return summary


if __name__ == "__main__":
    run_cli_eval()