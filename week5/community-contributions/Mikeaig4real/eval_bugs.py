"""
CLI for single-test bugs RAG evaluation.
Run from this directory: uv run python eval_bugs.py <test_row_number>
Uses evals/ (tests, retrieval metrics, answer judge) and implementation.answer.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from evals.test_loader import TestQuestion, load_tests
from evals.retrieval_metrics import RetrievalEval, evaluate_retrieval_from_docs
from evals.answer_eval import AnswerEval, evaluate_answer
from implementation.answer import fetch_context

load_dotenv(override=True)


def evaluate_retrieval(test: TestQuestion, k: int = 10) -> RetrievalEval:
    """Evaluate retrieval for one test using implementation.answer.fetch_context."""
    retrieved_docs = fetch_context(test.question)
    return evaluate_retrieval_from_docs(test.keywords, retrieved_docs, k=k)


def run_cli_evaluation(test_number: int):
    """Run retrieval + answer evaluation for one test (by row index)."""
    tests = load_tests()
    if test_number < 0 or test_number >= len(tests):
        print(f"Error: test_row_number must be between 0 and {len(tests) - 1}")
        sys.exit(1)
    test = tests[test_number]
    print(f"\n{'=' * 80}")
    print(f"Test #{test_number} (category: {test.category})")
    print(f"{'=' * 80}")
    print(f"Question: {test.question}")
    print(f"Keywords: {test.keywords}")
    print(f"Reference Answer: {test.reference_answer}")

    print(f"\n{'=' * 80}")
    print("Retrieval Evaluation")
    print(f"{'=' * 80}")
    retrieval_result = evaluate_retrieval(test)
    print(f"MRR: {retrieval_result.mrr:.4f}")
    print(f"nDCG: {retrieval_result.ndcg:.4f}")
    print(f"Keywords Found: {retrieval_result.keywords_found}/{retrieval_result.total_keywords}")
    print(f"Keyword Coverage: {retrieval_result.keyword_coverage:.1f}%")

    print(f"\n{'=' * 80}")
    print("Answer Evaluation")
    print(f"{'=' * 80}")
    answer_result, generated_answer, retrieved_docs = evaluate_answer(test)
    print(f"\nGenerated Answer:\n{generated_answer}")
    print(f"\nFeedback:\n{answer_result.feedback}")
    print("\nScores:")
    print(f"  Accuracy: {answer_result.accuracy:.2f}/5")
    print(f"  Completeness: {answer_result.completeness:.2f}/5")
    print(f"  Relevance: {answer_result.relevance:.2f}/5")
    print(f"\n{'=' * 80}\n")


def main():
    if len(sys.argv) != 2:
        print("Usage: uv run python eval_bugs.py <test_row_number>")
        print("  Run from week5/community-contributions/Mikeaig4real/")
        sys.exit(1)
    try:
        test_number = int(sys.argv[1])
    except ValueError:
        print("Error: test_row_number must be an integer")
        sys.exit(1)
    run_cli_evaluation(test_number)


if __name__ == "__main__":
    main()
