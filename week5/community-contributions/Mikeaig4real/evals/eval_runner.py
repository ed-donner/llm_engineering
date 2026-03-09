import logging

# Global log tracker toggle
LOG_TRACKER_ENABLED = False


"""
Evaluation runners: generators for retrieval and answer eval (used by Gradio evaluator).
Uses implementation.answer (fetch_context) and evals metrics.
"""
from evals.test_loader import load_tests, TestQuestion
from evals.retrieval_metrics import RetrievalEval, evaluate_retrieval_from_docs
from implementation.answer import fetch_context


def evaluate_retrieval(test: TestQuestion, k: int = 10) -> RetrievalEval:
    """Evaluate retrieval for one test using implementation.answer.fetch_context."""
    if LOG_TRACKER_ENABLED:
        logging.info(f"[LOG] Fetching context for question: {test.question}")
    retrieved_docs = fetch_context(test.question)
    if LOG_TRACKER_ENABLED:
        logging.info(
            f"[LOG] Retrieved {len(retrieved_docs) if hasattr(retrieved_docs, '__len__') else 'unknown'} docs for question: {test.question}"
        )
    return evaluate_retrieval_from_docs(test.keywords, retrieved_docs, k=k)


def evaluate_all_retrieval():
    """Yield (test, RetrievalEval result, progress 0..1) for each test."""
    tests = load_tests()
    total = len(tests)
    for index, test in enumerate(tests):
        if LOG_TRACKER_ENABLED:
            logging.info(f"[LOG] Evaluating retrieval for test {index+1}/{total}")
        result = evaluate_retrieval(test)
        progress = (index + 1) / total
        yield test, result, progress
