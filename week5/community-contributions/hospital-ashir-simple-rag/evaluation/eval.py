"""
RAG evaluation for the Hospital-Ashir knowledge base.

Computes:
  * Retrieval metrics  — MRR, nDCG, and keyword coverage against the top-k docs
  * Answer metrics     — LLM-as-a-judge scores for accuracy, completeness, relevance

Usage:
    # Evaluate a single test by row number (prints retrieval + answer eval)
    python evaluation/eval.py 0

    # Evaluate all retrieval tests and print aggregate metrics
    python evaluation/eval.py --all-retrieval

    # Evaluate all answers (costly - runs the LLM judge for every test)
    python evaluation/eval.py --all-answers
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from dotenv import load_dotenv
from litellm import completion
from pydantic import BaseModel, Field

# Make sibling package imports work regardless of where this script is run from.
CURRENT_DIR = Path(__file__).parent
HOSPITAL_DIR = CURRENT_DIR.parent
if str(HOSPITAL_DIR) not in sys.path:
    sys.path.insert(0, str(HOSPITAL_DIR))

from answer import answer_question, fetch_context  # noqa: E402
from evaluation.test import TestQuestion, load_tests  # noqa: E402


load_dotenv(override=True)

JUDGE_MODEL = "gpt-4.1-nano"
TOP_K = 12


class RetrievalEval(BaseModel):
    """Evaluation metrics for retrieval performance."""

    mrr: float = Field(description="Mean Reciprocal Rank - averaged over all keywords")
    ndcg: float = Field(
        description="Normalized Discounted Cumulative Gain (binary relevance)"
    )
    keywords_found: int = Field(description="Number of keywords found in top-k results")
    total_keywords: int = Field(description="Total number of keywords to find")
    keyword_coverage: float = Field(description="Percentage of keywords found (0-100)")


class AnswerEval(BaseModel):
    """LLM-as-a-judge evaluation of answer quality."""

    feedback: str = Field(
        description="Concise feedback on the answer quality, comparing it to the reference answer and evaluating based on the retrieved context"
    )
    accuracy: float = Field(
        description="How factually correct is the answer compared to the reference answer? 1 (wrong) to 5 (perfect)."
    )
    completeness: float = Field(
        description="How complete is the answer in addressing all aspects of the question? 1 (poor) to 5 (ideal)."
    )
    relevance: float = Field(
        description="How relevant is the answer to the specific question asked? 1 (off-topic) to 5 (perfectly relevant)."
    )


# ---------------------------------------------------------------------------
# Retrieval metrics
# ---------------------------------------------------------------------------

def calculate_mrr(keyword: str, retrieved_docs: list) -> float:
    """Reciprocal rank of the first doc that contains the keyword (case-insensitive)."""
    keyword_lower = keyword.lower()
    for rank, doc in enumerate(retrieved_docs, start=1):
        if keyword_lower in doc.page_content.lower():
            return 1.0 / rank
    return 0.0


def calculate_dcg(relevances: list[int], k: int) -> float:
    """Discounted Cumulative Gain over a ranked list of binary relevances."""
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        dcg += relevances[i] / math.log2(i + 2)  # i+2 because rank starts at 1
    return dcg


def calculate_ndcg(keyword: str, retrieved_docs: list, k: int = TOP_K) -> float:
    """Normalized DCG for a single keyword with binary relevance."""
    keyword_lower = keyword.lower()
    relevances = [
        1 if keyword_lower in doc.page_content.lower() else 0
        for doc in retrieved_docs[:k]
    ]
    dcg = calculate_dcg(relevances, k)
    idcg = calculate_dcg(sorted(relevances, reverse=True), k)
    return dcg / idcg if idcg > 0 else 0.0


def evaluate_retrieval(test: TestQuestion, k: int = TOP_K) -> RetrievalEval:
    """Score retrieval quality for a single test question."""
    retrieved_docs = fetch_context(test.question)

    mrr_scores = [calculate_mrr(kw, retrieved_docs) for kw in test.keywords]
    ndcg_scores = [calculate_ndcg(kw, retrieved_docs, k) for kw in test.keywords]

    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0

    keywords_found = sum(1 for s in mrr_scores if s > 0)
    total_keywords = len(test.keywords)
    keyword_coverage = (
        (keywords_found / total_keywords * 100) if total_keywords > 0 else 0.0
    )

    return RetrievalEval(
        mrr=avg_mrr,
        ndcg=avg_ndcg,
        keywords_found=keywords_found,
        total_keywords=total_keywords,
        keyword_coverage=keyword_coverage,
    )


# ---------------------------------------------------------------------------
# Answer quality metrics (LLM-as-a-judge)
# ---------------------------------------------------------------------------

def evaluate_answer(test: TestQuestion) -> tuple[AnswerEval, str, list]:
    """Evaluate answer quality using an LLM judge. Returns (scores, answer, docs)."""
    generated_answer, retrieved_docs = answer_question(test.question)

    judge_messages = [
        {
            "role": "system",
            "content": (
                "You are an expert evaluator assessing the quality of answers from a hospital "
                "information assistant. Compare the generated answer to the reference answer "
                "and judge it objectively. Only give 5/5 for perfect answers. If the answer "
                "is factually wrong, accuracy must be 1."
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

Please evaluate the generated answer on three dimensions:
1. Accuracy: How factually correct is it compared to the reference answer?
2. Completeness: Does it cover all the information from the reference answer?
3. Relevance: Does it directly answer the question without extra information?

Provide concise feedback and numeric scores 1 (very poor) to 5 (ideal) for each dimension.""",
        },
    ]

    judge_response = completion(
        model=JUDGE_MODEL,
        messages=judge_messages,
        response_format=AnswerEval,
    )

    answer_eval = AnswerEval.model_validate_json(
        judge_response.choices[0].message.content
    )
    return answer_eval, generated_answer, retrieved_docs


# ---------------------------------------------------------------------------
# Batch runners
# ---------------------------------------------------------------------------

def evaluate_all_retrieval():
    """Yield (test, RetrievalEval, progress) for every test question."""
    tests = load_tests()
    total = len(tests)
    for index, test in enumerate(tests):
        result = evaluate_retrieval(test)
        yield test, result, (index + 1) / total


def evaluate_all_answers():
    """Yield (test, AnswerEval, progress) for every test question."""
    tests = load_tests()
    total = len(tests)
    for index, test in enumerate(tests):
        result = evaluate_answer(test)[0]
        yield test, result, (index + 1) / total


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def run_cli_single(test_number: int) -> None:
    """Evaluate a single test by row number in tests.jsonl."""
    tests = load_tests()

    if test_number < 0 or test_number >= len(tests):
        print(f"Error: test index must be between 0 and {len(tests) - 1}")
        sys.exit(1)

    test = tests[test_number]

    print("\n" + "=" * 80)
    print(f"Test #{test_number}  [{test.category}]")
    print("=" * 80)
    print(f"Question: {test.question}")
    print(f"Keywords: {test.keywords}")
    print(f"Reference Answer: {test.reference_answer}")

    print("\n" + "=" * 80)
    print("Retrieval Evaluation")
    print("=" * 80)
    retrieval = evaluate_retrieval(test)
    print(f"MRR:              {retrieval.mrr:.4f}")
    print(f"nDCG:             {retrieval.ndcg:.4f}")
    print(
        f"Keywords Found:   {retrieval.keywords_found}/{retrieval.total_keywords}"
    )
    print(f"Keyword Coverage: {retrieval.keyword_coverage:.1f}%")

    print("\n" + "=" * 80)
    print("Answer Evaluation")
    print("=" * 80)
    answer_result, generated_answer, _ = evaluate_answer(test)
    print(f"\nGenerated Answer:\n{generated_answer}")
    print(f"\nFeedback:\n{answer_result.feedback}")
    print("\nScores:")
    print(f"  Accuracy:     {answer_result.accuracy:.2f}/5")
    print(f"  Completeness: {answer_result.completeness:.2f}/5")
    print(f"  Relevance:    {answer_result.relevance:.2f}/5")
    print()


def run_cli_all_retrieval() -> None:
    """Evaluate retrieval across every test and print per-category aggregates."""
    mrr_all: list[float] = []
    ndcg_all: list[float] = []
    coverage_all: list[float] = []
    per_category: dict[str, list[tuple[float, float, float]]] = {}

    print("\nRunning retrieval evaluation on every test...\n")
    for test, result, progress in evaluate_all_retrieval():
        mrr_all.append(result.mrr)
        ndcg_all.append(result.ndcg)
        coverage_all.append(result.keyword_coverage)
        per_category.setdefault(test.category, []).append(
            (result.mrr, result.ndcg, result.keyword_coverage)
        )
        pct = progress * 100
        print(
            f"[{pct:5.1f}%] {test.category:<16} MRR={result.mrr:.3f} "
            f"nDCG={result.ndcg:.3f} coverage={result.keyword_coverage:5.1f}%  "
            f"|  {test.question[:60]}"
        )

    print("\n" + "=" * 80)
    print("Aggregate Retrieval Metrics")
    print("=" * 80)
    print(f"Tests:             {len(mrr_all)}")
    print(f"Mean MRR:          {sum(mrr_all) / len(mrr_all):.4f}")
    print(f"Mean nDCG:         {sum(ndcg_all) / len(ndcg_all):.4f}")
    print(f"Mean Keyword Cov.: {sum(coverage_all) / len(coverage_all):.1f}%")

    print("\nBy category:")
    for category in sorted(per_category.keys()):
        scores = per_category[category]
        mrr = sum(s[0] for s in scores) / len(scores)
        ndcg = sum(s[1] for s in scores) / len(scores)
        cov = sum(s[2] for s in scores) / len(scores)
        print(
            f"  {category:<16} n={len(scores):<3} "
            f"MRR={mrr:.3f}  nDCG={ndcg:.3f}  coverage={cov:5.1f}%"
        )
    print()


def run_cli_all_answers() -> None:
    """Evaluate answers across every test using the LLM judge (expensive)."""
    accuracy_all: list[float] = []
    completeness_all: list[float] = []
    relevance_all: list[float] = []

    print("\nRunning LLM-as-judge answer evaluation on every test...\n")
    for test, result, progress in evaluate_all_answers():
        accuracy_all.append(result.accuracy)
        completeness_all.append(result.completeness)
        relevance_all.append(result.relevance)
        pct = progress * 100
        print(
            f"[{pct:5.1f}%] {test.category:<16} "
            f"acc={result.accuracy:.1f}  comp={result.completeness:.1f}  "
            f"rel={result.relevance:.1f}  |  {test.question[:60]}"
        )

    n = len(accuracy_all)
    print("\n" + "=" * 80)
    print("Aggregate Answer Metrics")
    print("=" * 80)
    print(f"Tests:             {n}")
    print(f"Mean Accuracy:     {sum(accuracy_all) / n:.2f} / 5")
    print(f"Mean Completeness: {sum(completeness_all) / n:.2f} / 5")
    print(f"Mean Relevance:    {sum(relevance_all) / n:.2f} / 5")
    print()


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  python evaluation/eval.py <test_row_number>\n"
            "  python evaluation/eval.py --all-retrieval\n"
            "  python evaluation/eval.py --all-answers"
        )
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--all-retrieval":
        run_cli_all_retrieval()
        return
    if arg == "--all-answers":
        run_cli_all_answers()
        return

    try:
        test_number = int(arg)
    except ValueError:
        print("Error: first argument must be an integer or --all-retrieval / --all-answers")
        sys.exit(1)

    run_cli_single(test_number)


if __name__ == "__main__":
    main()
