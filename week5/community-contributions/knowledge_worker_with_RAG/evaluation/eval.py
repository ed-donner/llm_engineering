import math
import sys
from pathlib import Path

from dotenv import load_dotenv
from litellm import completion
from pydantic import BaseModel, Field

from test import TestQuestion, load_tests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from answer import answer_question, fetch_context  # noqa: E402

load_dotenv(override=True)

JUDGE_MODEL = "openai/gpt-4o-mini"


class RetrievalEval(BaseModel):
    """Evaluation metrics for retrieval quality."""

    mrr: float = Field(description="Mean Reciprocal Rank across all keywords")
    ndcg: float = Field(description="Normalized Discounted Cumulative Gain (binary relevance)")
    keywords_found: int = Field(description="How many expected keywords were found in top-k results")
    total_keywords: int = Field(description="How many expected keywords were provided")
    keyword_coverage: float = Field(description="Percent of expected keywords found")


class AnswerEval(BaseModel):
    """LLM-as-a-judge metrics for answer quality."""

    feedback: str = Field(description="Short feedback for quality, correctness, and relevance")
    accuracy: float = Field(description="1-5 score for factual correctness vs reference answer")
    completeness: float = Field(description="1-5 score for coverage of key points")
    relevance: float = Field(description="1-5 score for directness and focus")


def calculate_mrr(keyword: str, retrieved_docs: list) -> float:
    keyword_lower = keyword.lower()
    for rank, doc in enumerate(retrieved_docs, start=1):
        if keyword_lower in doc.page_content.lower():
            return 1.0 / rank
    return 0.0


def calculate_dcg(relevances: list[int], k: int) -> float:
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        dcg += relevances[i] / math.log2(i + 2)
    return dcg


def calculate_ndcg(keyword: str, retrieved_docs: list, k: int = 10) -> float:
    keyword_lower = keyword.lower()
    relevances = [1 if keyword_lower in doc.page_content.lower() else 0 for doc in retrieved_docs[:k]]
    dcg = calculate_dcg(relevances, k)
    idcg = calculate_dcg(sorted(relevances, reverse=True), k)
    return dcg / idcg if idcg > 0 else 0.0


def evaluate_retrieval(test: TestQuestion, k: int = 10) -> RetrievalEval:
    retrieved_docs = fetch_context(test.question, k=k)
    mrr_scores = [calculate_mrr(keyword, retrieved_docs) for keyword in test.keywords]
    ndcg_scores = [calculate_ndcg(keyword, retrieved_docs, k=k) for keyword in test.keywords]
    keywords_found = sum(1 for score in mrr_scores if score > 0)
    total_keywords = len(test.keywords)
    keyword_coverage = (keywords_found / total_keywords * 100.0) if total_keywords else 0.0
    return RetrievalEval(
        mrr=(sum(mrr_scores) / len(mrr_scores)) if mrr_scores else 0.0,
        ndcg=(sum(ndcg_scores) / len(ndcg_scores)) if ndcg_scores else 0.0,
        keywords_found=keywords_found,
        total_keywords=total_keywords,
        keyword_coverage=keyword_coverage,
    )


def evaluate_answer(test: TestQuestion) -> tuple[AnswerEval, str, list]:
    generated_answer, retrieved_docs = answer_question(test.question)
    judge_messages = [
        {
            "role": "system",
            "content": (
                "You are an expert evaluator of RAG answers. "
                "Score strictly from 1 to 5. Give 5 only for near-perfect quality."
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

Evaluate:
1) Accuracy (1-5)
2) Completeness (1-5)
3) Relevance (1-5)

Also provide short feedback.
""",
        },
    ]
    judge_response = completion(model=JUDGE_MODEL, messages=judge_messages, response_format=AnswerEval)
    answer_eval = AnswerEval.model_validate_json(judge_response.choices[0].message.content)
    return answer_eval, generated_answer, retrieved_docs


def run_cli_evaluation(test_number: int) -> None:
    tests = load_tests()
    if test_number < 0 or test_number >= len(tests):
        print(f"Error: test_row_number must be between 0 and {len(tests) - 1}")
        sys.exit(1)

    test = tests[test_number]
    print(f"\n{'=' * 80}")
    print(f"Test #{test_number}")
    print(f"{'=' * 80}")
    print(f"Question: {test.question}")
    print(f"Keywords: {test.keywords}")
    print(f"Category: {test.category}")
    print(f"Reference Answer: {test.reference_answer}")

    retrieval_result = evaluate_retrieval(test)
    print(f"\n{'=' * 80}")
    print("Retrieval Evaluation")
    print(f"{'=' * 80}")
    print(f"MRR: {retrieval_result.mrr:.4f}")
    print(f"nDCG: {retrieval_result.ndcg:.4f}")
    print(f"Keywords Found: {retrieval_result.keywords_found}/{retrieval_result.total_keywords}")
    print(f"Keyword Coverage: {retrieval_result.keyword_coverage:.1f}%")

    answer_result, generated_answer, _ = evaluate_answer(test)
    print(f"\n{'=' * 80}")
    print("Answer Evaluation")
    print(f"{'=' * 80}")
    print(f"\nGenerated Answer:\n{generated_answer}")
    print(f"\nFeedback:\n{answer_result.feedback}")
    print("\nScores:")
    print(f"  Accuracy: {answer_result.accuracy:.2f}/5")
    print(f"  Completeness: {answer_result.completeness:.2f}/5")
    print(f"  Relevance: {answer_result.relevance:.2f}/5")
    print(f"\n{'=' * 80}\n")


def run_all_evaluations() -> None:
    """Run retrieval + answer evaluation for all tests and print aggregate metrics."""
    tests = load_tests()
    if not tests:
        print("No tests found in evaluation/tests.jsonl")
        sys.exit(1)

    retrieval_results: list[RetrievalEval] = []
    answer_results: list[AnswerEval] = []

    print(f"\n{'=' * 80}")
    print(f"Running full evaluation on {len(tests)} tests")
    print(f"{'=' * 80}")

    for idx, test in enumerate(tests):
        print(f"\n[{idx}] {test.question}")
        retrieval = evaluate_retrieval(test)
        answer, _, _ = evaluate_answer(test)
        retrieval_results.append(retrieval)
        answer_results.append(answer)
        print(
            "  Retrieval -> "
            f"MRR: {retrieval.mrr:.3f}, "
            f"nDCG: {retrieval.ndcg:.3f}, "
            f"Coverage: {retrieval.keyword_coverage:.1f}%"
        )
        print(
            "  Answer    -> "
            f"Accuracy: {answer.accuracy:.2f}, "
            f"Completeness: {answer.completeness:.2f}, "
            f"Relevance: {answer.relevance:.2f}"
        )

    total = len(tests)
    avg_mrr = sum(r.mrr for r in retrieval_results) / total
    avg_ndcg = sum(r.ndcg for r in retrieval_results) / total
    avg_cov = sum(r.keyword_coverage for r in retrieval_results) / total
    avg_acc = sum(a.accuracy for a in answer_results) / total
    avg_compl = sum(a.completeness for a in answer_results) / total
    avg_rel = sum(a.relevance for a in answer_results) / total

    print(f"\n{'=' * 80}")
    print("Aggregate Metrics")
    print(f"{'=' * 80}")
    print(f"Retrieval: MRR={avg_mrr:.4f} | nDCG={avg_ndcg:.4f} | Coverage={avg_cov:.1f}%")
    print(
        f"Answer: Accuracy={avg_acc:.2f}/5 | "
        f"Completeness={avg_compl:.2f}/5 | Relevance={avg_rel:.2f}/5"
    )
    print(f"{'=' * 80}\n")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: uv run evaluation/eval.py <test_row_number|--all>")
        sys.exit(1)

    arg = sys.argv[1].strip().lower()
    if arg == "--all":
        run_all_evaluations()
        return

    try:
        test_number = int(arg)
    except ValueError:
        print("Error: test_row_number must be an integer, or use --all")
        sys.exit(1)
    run_cli_evaluation(test_number)


if __name__ == "__main__":
    main()
