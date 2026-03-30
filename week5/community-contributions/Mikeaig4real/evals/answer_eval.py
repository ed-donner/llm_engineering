"""
Answer evaluation: LLM-as-a-judge for bugs RAG. Self-contained in evals (no week5 dependency).
"""

import os
from pydantic import BaseModel, Field
from litellm import completion
from dotenv import load_dotenv
import logging

load_dotenv(override=True)

# Global log tracker toggle
LOG_TRACKER_ENABLED = False

# implementation.* is resolved when run from Mikeaig4real (path on sys.path)
from evals.test_loader import TestQuestion  # noqa: I001
from implementation.answer import answer_question

JUDGE_MODEL = os.getenv("EVAL_MODEL", "openrouter/openai/gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY") or ""


class AnswerEval(BaseModel):
    """LLM-as-a-judge evaluation of answer quality."""

    feedback: str = Field(
        description="Concise feedback on the answer quality, comparing it to the reference answer"
    )
    accuracy: float = Field(
        description="Factual correctness vs reference, 1 (wrong) to 5 (ideal)"
    )
    completeness: float = Field(
        description="How complete the answer is, 1 (poor) to 5 (ideal)"
    )
    relevance: float = Field(
        description="How relevant to the question, 1 (poor) to 5 (ideal)"
    )


def evaluate_answer(test: TestQuestion) -> tuple[AnswerEval, str, list]:
    """Run RAG answer then LLM judge. Returns (AnswerEval, generated_answer, retrieved_docs)."""
    if LOG_TRACKER_ENABLED:
        logging.info(f"[LOG] Generating answer for question: {test.question}")
    generated_answer, retrieved_docs = answer_question(test.question)
    if LOG_TRACKER_ENABLED:
        logging.info(f"[LOG] Generated answer: {generated_answer}")
        logging.info(
            f"[LOG] Retrieved {len(retrieved_docs) if hasattr(retrieved_docs, '__len__') else 'unknown'} docs for answer evaluation."
        )
    judge_messages = [
        {
            "role": "system",
            "content": "You are an expert evaluator assessing the quality of answers. Evaluate the generated answer by comparing it to the reference answer. Only give 5/5 scores for perfect answers.",
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
1. Accuracy: How factually correct is it compared to the reference answer? Only give 5/5 scores for perfect answers.
2. Completeness: How thoroughly does it address all aspects of the question, covering all the information from the reference answer?
3. Relevance: How well does it directly answer the specific question asked, giving no additional information?

Provide detailed feedback and scores from 1 (very poor) to 5 (ideal) for each dimension. If the answer is wrong, then the accuracy score must be 1.""",
        },
    ]
    kwargs = {
        "model": JUDGE_MODEL,
        "messages": judge_messages,
        "response_format": AnswerEval,
    }
    if API_KEY:
        kwargs["api_key"] = API_KEY
    resp = completion(**kwargs)
    answer_eval = AnswerEval.model_validate_json(resp.choices[0].message.content)
    return answer_eval, generated_answer, retrieved_docs


def evaluate_all_answers():
    """Yield (test, AnswerEval result, progress 0..1) for each test."""
    from evals.test_loader import load_tests  # avoid circular import at module load

    tests = load_tests()
    total = len(tests)
    for index, test in enumerate(tests):
        result, _, _ = evaluate_answer(test)
        progress = (index + 1) / total
        yield test, result, progress
