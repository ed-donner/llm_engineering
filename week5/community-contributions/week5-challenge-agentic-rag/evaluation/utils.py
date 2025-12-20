from __future__ import annotations

from typing import Callable, Iterable, Sequence

import math
from litellm import completion
from pydantic import BaseModel, Field

from evaluation.test import TestQuestion


class RetrievalEval(BaseModel):
    """Evaluation metrics for retrieval performance."""

    mrr: float = Field(description="Mean Reciprocal Rank - average across all keywords")
    ndcg: float = Field(description="Normalized Discounted Cumulative Gain (binary relevance)")
    keywords_found: int = Field(description="Number of keywords found in top-k results")
    total_keywords: int = Field(description="Total number of keywords to find")
    keyword_coverage: float = Field(description="Percentage of keywords found")


class AnswerEval(BaseModel):
    """LLM-as-a-judge evaluation of answer quality."""

    feedback: str = Field(
        description=(
            "Concise feedback on the answer quality, comparing it to the reference answer "
            "and evaluating based on the retrieved context"
        )
    )
    accuracy: float = Field(
        description=(
            "How factually correct is the answer compared to the reference answer? 1 (wrong. any wrong "
            "answer must score 1) to 5 (ideal - perfectly accurate). An acceptable answer would score 3."
        )
    )
    completeness: float = Field(
        description=(
            "How complete is the answer in addressing all aspects of the question? 1 (very poor - missing "
            "key information) to 5 (ideal - all the information from the reference answer is provided completely). "
            "Only answer 5 if ALL information from the reference answer is included."
        )
    )
    relevance: float = Field(
        description=(
            "How relevant is the answer to the specific question asked? 1 (very poor - off-topic) to 5 (ideal - "
            "directly addresses question and gives no additional information). Only answer 5 if the answer is "
            "completely relevant to the question and gives no additional information."
        )
    )


def calculate_mrr(keyword: str, retrieved_docs: Sequence) -> float:
    """Calculate reciprocal rank for a single keyword (case-insensitive)."""
    keyword_lower = keyword.lower()
    for rank, doc in enumerate(retrieved_docs, start=1):
        if keyword_lower in doc.page_content.lower():
            return 1.0 / rank
    return 0.0


def calculate_dcg(relevances: Sequence[int], k: int) -> float:
    """Calculate Discounted Cumulative Gain."""
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        dcg += relevances[i] / math.log2(i + 2)  # i+2 because rank starts at 1
    return dcg


def calculate_ndcg(keyword: str, retrieved_docs: Sequence, k: int = 10) -> float:
    """Calculate nDCG for a single keyword (binary relevance, case-insensitive)."""
    keyword_lower = keyword.lower()

    # Binary relevance: 1 if keyword found, 0 otherwise
    relevances = [
        1 if keyword_lower in doc.page_content.lower() else 0 for doc in retrieved_docs[:k]
    ]

    # DCG
    dcg = calculate_dcg(relevances, k)

    # Ideal DCG (best case: keyword in first position)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = calculate_dcg(ideal_relevances, k)

    return dcg / idcg if idcg > 0 else 0.0


def run_retrieval_evaluation(
    test: TestQuestion, fetch_context_fn: Callable[[str], Iterable], k: int = 10
) -> RetrievalEval:
    """
    Evaluate retrieval performance for a test question.

    Args:
        test: TestQuestion object containing question and keywords
        fetch_context_fn: callable that accepts the test question and returns retrieved docs
        k: Number of top documents to consider
    """
    retrieved_docs = fetch_context_fn(test.question)

    mrr_scores = [calculate_mrr(keyword, retrieved_docs) for keyword in test.keywords]
    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0

    ndcg_scores = [calculate_ndcg(keyword, retrieved_docs, k) for keyword in test.keywords]
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0

    keywords_found = sum(1 for score in mrr_scores if score > 0)
    total_keywords = len(test.keywords)
    keyword_coverage = (keywords_found / total_keywords * 100) if total_keywords > 0 else 0.0

    return RetrievalEval(
        mrr=avg_mrr,
        ndcg=avg_ndcg,
        keywords_found=keywords_found,
        total_keywords=total_keywords,
        keyword_coverage=keyword_coverage,
    )


def score_answer(
    question: str, generated_answer: str, reference_answer: str, *, model: str
) -> AnswerEval:
    """Score an answer against a provided reference answer using LLM-as-a-judge."""

    judge_messages = [
        {
            "role": "system",
            "content": (
                "You are an expert evaluator assessing the quality of answers. "
                "Evaluate the generated answer by comparing it to the reference answer. "
                "Only give 5/5 scores for perfect answers."
            ),
        },
        {
            "role": "user",
            "content": f"""Question:
{question}

Generated Answer:
{generated_answer}

Reference Answer:
{reference_answer}

Please evaluate the generated answer on three dimensions:
1. Accuracy: How factually correct is it compared to the reference answer? Only give 5/5 scores for perfect answers.
2. Completeness: How thoroughly does it address all aspects of the question, covering all the information from the reference answer?
3. Relevance: How well does it directly answer the specific question asked, giving no additional information?

Provide detailed feedback and scores from 1 (very poor) to 5 (ideal) for each dimension. If the answer is wrong, then the accuracy score must be 1.""",
        },
    ]

    judge_response = completion(model=model, messages=judge_messages, response_format=AnswerEval)
    return AnswerEval.model_validate_json(judge_response.choices[0].message.content)


def run_answer_evaluation(
    test: TestQuestion,
    answer_fn: Callable[[str], tuple[str, Sequence]],
    *,
    judge_model: str,
) -> tuple[AnswerEval, str, Sequence]:
    """Evaluate a generated answer compared to the reference answer defined in the test."""
    generated_answer, retrieved_docs = answer_fn(test.question)
    answer_eval = score_answer(
        test.question,
        generated_answer,
        test.reference_answer,
        model=judge_model,
    )
    return answer_eval, generated_answer, retrieved_docs
