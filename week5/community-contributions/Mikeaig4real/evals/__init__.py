"""
Bugs RAG evaluation: test loader, retrieval metrics, answer judge, Gradio dashboard.
Use from notebook or CLI with Mikeaig4real on sys.path.
"""
from evals.test_loader import TestQuestion, load_tests
from evals.retrieval_metrics import RetrievalEval, evaluate_retrieval_from_docs
from evals.answer_eval import AnswerEval, evaluate_answer, evaluate_all_answers
from evals.eval_runner import evaluate_retrieval, evaluate_all_retrieval
from evals.evaluator import launch

__all__ = [
    "TestQuestion",
    "load_tests",
    "RetrievalEval",
    "evaluate_retrieval_from_docs",
    "AnswerEval",
    "evaluate_answer",
    "evaluate_all_answers",
    "evaluate_retrieval",
    "evaluate_all_retrieval",
    "launch",
]
