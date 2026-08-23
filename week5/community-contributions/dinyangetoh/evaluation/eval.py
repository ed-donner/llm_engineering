import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

from evaluation.test import TestQuestion, load_tests

load_dotenv(override=True)

_default_judge_client: OpenAI | None = None
_default_judge_model: str = "gpt-4.1-nano"


def set_judge_client(client: OpenAI | None, model: str | None = None) -> None:
    global _default_judge_client, _default_judge_model
    _default_judge_client = client
    if model is not None:
        _default_judge_model = model


# ---------------------------------------------------------------------------
# Pydantic result models
# ---------------------------------------------------------------------------

class RetrievalEval(BaseModel):
    mrr: float = Field(
        description="Mean Reciprocal Rank - average across all keywords")
    ndcg: float = Field(
        description="Normalized Discounted Cumulative Gain (binary relevance)")
    keywords_found: int = Field(
        description="Number of keywords found in top-k results")
    total_keywords: int = Field(description="Total number of keywords to find")
    keyword_coverage: float = Field(description="Percentage of keywords found")


class AnswerEval(BaseModel):
    feedback: str = Field(
        description="Concise feedback on answer quality vs reference")
    accuracy: float = Field(description="Factual correctness 1-5")
    completeness: float = Field(description="Completeness 1-5")
    relevance: float = Field(description="Relevance to question 1-5")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _doc_text(doc) -> str:
    """Return the text content of a retrieved document or plain string."""
    if hasattr(doc, "page_content"):
        return str(doc.page_content)
    return str(doc)


def _calculate_mrr(keyword: str, retrieved_docs: list) -> float:
    keyword_lower = keyword.lower()
    for rank, doc in enumerate(retrieved_docs, start=1):
        if keyword_lower in _doc_text(doc).lower():
            return 1.0 / rank
    return 0.0


def _calculate_dcg(relevances: list[int], k: int) -> float:
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        dcg += relevances[i] / math.log2(i + 2)
    return dcg


def _calculate_ndcg(keyword: str, retrieved_docs: list, k: int = 10) -> float:
    keyword_lower = keyword.lower()
    relevances = [
        1 if keyword_lower in _doc_text(doc).lower() else 0
        for doc in retrieved_docs[:k]
    ]
    dcg = _calculate_dcg(relevances, k)
    idcg = _calculate_dcg(sorted(relevances, reverse=True), k)
    return dcg / idcg if idcg > 0 else 0.0


def _get_judge_client(client: OpenAI | None) -> OpenAI:
    """Return the judge client, falling back to the module default then plain OpenAI()."""
    if client is not None:
        return client
    if _default_judge_client is not None:
        return _default_judge_client
    return OpenAI()


def _get_judge_model(model: str | None) -> str:
    """Return the judge model name, falling back to the module default."""
    return model if model is not None else _default_judge_model


# ---------------------------------------------------------------------------
# Public eval functions
# ---------------------------------------------------------------------------

def evaluate_retrieval(
    test: TestQuestion,
    fetch_context_fn,
    k: int = 10,
) -> RetrievalEval:
    retrieved_docs = fetch_context_fn(test.question, k=k)
    mrr_scores = [_calculate_mrr(kw, retrieved_docs) for kw in test.keywords]
    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0
    ndcg_scores = [_calculate_ndcg(kw, retrieved_docs, k)
                   for kw in test.keywords]
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0
    keywords_found = sum(1 for s in mrr_scores if s > 0)
    total_keywords = len(test.keywords)
    keyword_coverage = (keywords_found / total_keywords *
                        100) if total_keywords else 0.0
    return RetrievalEval(
        mrr=avg_mrr,
        ndcg=avg_ndcg,
        keywords_found=keywords_found,
        total_keywords=total_keywords,
        keyword_coverage=keyword_coverage,
    )


def evaluate_answer(
    test: TestQuestion,
    get_answer_fn,
    model: str | None = None,
    client: OpenAI | None = None,
) -> tuple[AnswerEval, str]:
    generated_answer = get_answer_fn(test.question)
    judge_client = _get_judge_client(client)
    judge_model = _get_judge_model(model)

    judge_messages = [
        {
            "role": "system",
            "content": (
                "You are an expert evaluator. Compare the generated answer to the reference. "
                "Only give 5/5 for perfect answers. "
                "Output valid JSON with keys: feedback, accuracy, completeness, relevance (all numbers 1-5)."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {test.question}\n\n"
                f"Generated Answer: {generated_answer}\n\n"
                f"Reference Answer: {test.reference_answer}\n\n"
                "Evaluate on: 1) Accuracy (factually correct vs reference) "
                "2) Completeness (covers all aspects) 3) Relevance (directly answers question). "
                'If wrong, accuracy must be 1. Reply with JSON only: '
                '{"feedback": "...", "accuracy": N, "completeness": N, "relevance": N}'
            ),
        },
    ]

    response = judge_client.chat.completions.create(
        model=judge_model,
        messages=judge_messages,
        response_format={"type": "json_object"},

    )
    raw = response.choices[0].message.content or ""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"feedback": raw, "accuracy": 3.0,
                "completeness": 3.0, "relevance": 3.0}

    answer_eval = AnswerEval(
        feedback=str(data.get("feedback", "")),
        accuracy=float(data.get("accuracy", 3)),
        completeness=float(data.get("completeness", 3)),
        relevance=float(data.get("relevance", 3)),
    )
    return answer_eval, generated_answer


def _run_one_test(
    test: TestQuestion,
    fetch_context_fn,
    get_answer_fn,
    k_retrieval: int,
    judge_client: OpenAI | None,
    judge_model: str | None,
) -> tuple[float, float, float, float, float, dict]:
    ret = evaluate_retrieval(test, fetch_context_fn, k=k_retrieval)
    ans_eval, _ = evaluate_answer(
        test, get_answer_fn, model=judge_model, client=judge_client
    )
    row = {
        "category": test.category,
        "mrr": ret.mrr,
        "keyword_coverage": ret.keyword_coverage,
        "accuracy": ans_eval.accuracy,
        "completeness": ans_eval.completeness,
        "relevance": ans_eval.relevance,
    }
    return ret.mrr, ret.keyword_coverage, ans_eval.accuracy, ans_eval.completeness, ans_eval.relevance, row


def run_eval_summary(
    fetch_context_fn,
    get_answer_fn,
    k_retrieval: int = 10,
    judge_client: OpenAI | None = None,
    judge_model: str | None = None,
    tests: list[TestQuestion] | None = None,
    max_workers: int = 4,
) -> dict:
    if tests is None:
        tests = load_tests()
    if not tests:
        return {
            "retrieval": {"avg_mrr": 0.0, "avg_keyword_coverage_pct": 0.0},
            "answer": {"avg_accuracy": 0.0, "avg_completeness": 0.0, "avg_relevance": 0.0},
            "n_tests": 0,
            "per_test": [],
        }

    ret_mrrs: list[float] = []
    ret_coverages: list[float] = []
    ans_accuracy: list[float] = []
    ans_completeness: list[float] = []
    ans_relevance: list[float] = []
    per_test: list[dict] = []

    if max_workers <= 1:
        for test in tests:
            mrr, cov, acc, comp, rel, row = _run_one_test(
                test, fetch_context_fn, get_answer_fn, k_retrieval, judge_client, judge_model
            )
            ret_mrrs.append(mrr)
            ret_coverages.append(cov)
            ans_accuracy.append(acc)
            ans_completeness.append(comp)
            ans_relevance.append(rel)
            per_test.append(row)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    _run_one_test,
                    test,
                    fetch_context_fn,
                    get_answer_fn,
                    k_retrieval,
                    judge_client,
                    judge_model,
                ): i
                for i, test in enumerate(tests)
            }
            results = [None] * len(tests)
            for fut in as_completed(futures):
                i = futures[fut]
                results[i] = fut.result()
        for mrr, cov, acc, comp, rel, row in results:
            ret_mrrs.append(mrr)
            ret_coverages.append(cov)
            ans_accuracy.append(acc)
            ans_completeness.append(comp)
            ans_relevance.append(rel)
            per_test.append(row)

    n = len(tests)
    return {
        "retrieval": {
            "avg_mrr": sum(ret_mrrs) / n,
            "avg_keyword_coverage_pct": sum(ret_coverages) / n,
        },
        "answer": {
            "avg_accuracy": sum(ans_accuracy) / n,
            "avg_completeness": sum(ans_completeness) / n,
            "avg_relevance": sum(ans_relevance) / n,
        },
        "n_tests": n,
        "per_test": per_test,
    }
