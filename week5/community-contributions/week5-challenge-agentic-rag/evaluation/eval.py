import sys
from pathlib import Path

from dotenv import load_dotenv

# Ensure local evaluation package imports work when running as a script.
EVAL_DIR = Path(__file__).resolve().parent
CHALLENGE_ROOT = EVAL_DIR.parent
if str(CHALLENGE_ROOT) not in sys.path:
    sys.path.append(str(CHALLENGE_ROOT))

from evaluation.test import TestQuestion, load_tests
from evaluation.utils import (
    AnswerEval,
    RetrievalEval,
    run_answer_evaluation,
    run_retrieval_evaluation,
)
from implementation.answer import answer_question


load_dotenv(override=True)

MODEL = "gpt-4.1-nano"


def evaluate_retrieval(test: TestQuestion, k: int = 10) -> RetrievalEval:
    """Run retrieval metrics using the agentic pipeline's final chunk set."""

    def agent_chunk_supplier(question: str):
        _, chunks = answer_question(question)
        return chunks

    return run_retrieval_evaluation(test, agent_chunk_supplier, k)


def evaluate_answer(test: TestQuestion) -> tuple[AnswerEval, str, list]:
    """Proxy to run the shared answer evaluation helper with our answer_question implementation."""
    return run_answer_evaluation(
        test,
        lambda q: answer_question(q),
        judge_model=MODEL,
    )


def evaluate_all_retrieval():
    """Evaluate all retrieval tests."""
    tests = load_tests()
    total_tests = len(tests)
    for index, test in enumerate(tests):
        result = evaluate_retrieval(test)
        progress = (index + 1) / total_tests
        yield test, result, progress


def evaluate_all_answers():
    """Evaluate all answers to tests using batched async execution."""
    tests = load_tests()
    total_tests = len(tests)
    for index, test in enumerate(tests):
        result = evaluate_answer(test)[0]
        progress = (index + 1) / total_tests
        yield test, result, progress


def run_cli_evaluation(test_number: int):
    """Run evaluation for a specific test (async helper for CLI)."""
    # Load tests
    tests = load_tests()

    if test_number < 0 or test_number >= len(tests):
        print(f"Error: test_row_number must be between 0 and {len(tests) - 1}")
        sys.exit(1)

    # Get the test
    test = tests[test_number]

    # Print test info
    print(f"\n{'=' * 80}")
    print(f"Test #{test_number}")
    print(f"{'=' * 80}")
    print(f"Question: {test.question}")
    print(f"Keywords: {test.keywords}")
    print(f"Category: {test.category}")
    print(f"Reference Answer: {test.reference_answer}")

    # Answer Evaluation
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
    """CLI to evaluate a specific test by row number."""
    if len(sys.argv) != 2:
        print("Usage: uv run eval.py <test_row_number>")
        sys.exit(1)

    try:
        test_number = int(sys.argv[1])
    except ValueError:
        print("Error: test_row_number must be an integer")
        sys.exit(1)

    run_cli_evaluation(test_number)


if __name__ == "__main__":
    main()
