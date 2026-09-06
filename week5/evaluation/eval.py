import sys
import math
from pydantic import BaseModel, Field, field_validator
from litellm import completion
from dotenv import load_dotenv

from evaluation.test import TestQuestion, load_tests
from implementation.answer import answer_question, fetch_context

load_dotenv(override=True)

# ============ USE LM STUDIO FOR EVALUATION ============
EVAL_MODEL = "openai/gpt-oss-20b"
LM_STUDIO_EVAL_CONFIG = {
    "api_base": "http://127.0.0.1:1234/v1",
    "api_key": "not-needed",
    "custom_llm_provider": "openai",
}
# ======================================================

db_name = "vector_db"


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
        description="Concise feedback on the answer quality, comparing it to the reference answer."
    )
    accuracy: float = Field(
        ge=1.0,
        le=5.0,
        description="Accuracy score from 1.0 (completely wrong) to 5.0 (perfectly accurate)."
    )
    completeness: float = Field(
        ge=1.0,
        le=5.0,
        description="Completeness score from 1.0 (missing key info) to 5.0 (all information covered)."
    )
    relevance: float = Field(
        ge=1.0,
        le=5.0,
        description="Relevance score from 1.0 (completely off-topic) to 5.0 (direct and concise)."
    )

    @field_validator("accuracy", "completeness", "relevance", mode="before")
    @classmethod
    def normalize_scores(cls, value: float | int) -> float:
        """Normalize scores if the model outputs numbers outside 1.0 to 5.0."""
        val = float(value)
        if val > 100.0:
            val = val / 200.0
        elif val > 5.0:
            val = val / 20.0
        return max(1.0, min(5.0, round(val, 2)))


def calculate_mrr(keyword: str, retrieved_docs: list) -> float:
    """Calculate reciprocal rank for a single keyword (case-insensitive)."""
    keyword_lower = keyword.lower()
    for rank, doc in enumerate(retrieved_docs, start=1):
        if keyword_lower in doc.page_content.lower():
            return 1.0 / rank
    return 0.0


def calculate_dcg(relevances: list[int], k: int) -> float:
    """Calculate Discounted Cumulative Gain."""
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        dcg += relevances[i] / math.log2(i + 2)
    return dcg


def calculate_ndcg(keyword: str, retrieved_docs: list, k: int = 10) -> float:
    """Calculate nDCG for a single keyword (binary relevance, case-insensitive)."""
    keyword_lower = keyword.lower()
    relevances = [
        1 if keyword_lower in doc.page_content.lower() else 0 for doc in retrieved_docs[:k]
    ]
    dcg = calculate_dcg(relevances, k)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = calculate_dcg(ideal_relevances, k)
    return dcg / idcg if idcg > 0 else 0.0


def evaluate_retrieval(test: TestQuestion, k: int = 10) -> RetrievalEval:
    """Evaluate retrieval performance for a test question."""
    retrieved_docs = fetch_context(test.question)
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


def evaluate_answer(test: TestQuestion) -> tuple[AnswerEval, str, list]:
    """Evaluate answer quality using LLM-as-a-judge with LM Studio."""
    generated_answer, retrieved_docs = answer_question(test.question)

    judge_messages = [
        {
            "role": "system",
            "content": (
                "You are an expert evaluator. Evaluate the generated answer compared to the reference answer. "
                "Check whether mandatory keywords are present in the response where appropriate. "
                "All scores (accuracy, completeness, relevance) MUST be floating-point values strictly between 1.0 and 5.0."
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

Expected Keywords:
{test.keywords}

Score each dimension strictly from 1.0 (very poor) to 5.0 (ideal):
1. Accuracy: 1.0 to 5.0 (If the answer is factually wrong, score must be 1.0)
2. Completeness: 1.0 to 5.0 (Only 5.0 if all reference details and expected keywords are addressed)
3. Relevance: 1.0 to 5.0 (Only 5.0 if directly on-topic with no filler)

Provide clear feedback and numerical float scores between 1.0 and 5.0.""",
        },
    ]

    judge_response = completion(
        model=EVAL_MODEL,
        messages=judge_messages,
        response_format=AnswerEval,
        **LM_STUDIO_EVAL_CONFIG
    )

    answer_eval = AnswerEval.model_validate_json(judge_response.choices[0].message.content)
    return answer_eval, generated_answer, retrieved_docs


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
    """Run evaluation for a specific test (helper for CLI)."""
    tests = load_tests()
    if test_number < 0 or test_number >= len(tests):
        print(f"Error: test_number must be between 0 and {len(tests) - 1}")
        sys.exit(1)
    test = tests[test_number]
    print(f"\n{'=' * 80}")
    print(f"Test #{test_number}")
    print(f"{'=' * 80}")
    print(f"Question: {test.question}")
    print(f"Keywords: {test.keywords}")
    print(f"Category: {test.category}")
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