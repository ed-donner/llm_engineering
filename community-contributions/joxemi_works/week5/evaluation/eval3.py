"""
Evaluation script for the pro implementation using local Ollama generation and judge models.
"""

import sys
import math
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from evaluation.test3 import TestQuestion, load_tests
from pro_implementation.asnwer3 import answer_question, fetch_context


load_dotenv(override=True)

GENERATION_MODEL = "qwen2.5:7b-instruct"
JUDGE_MODEL = "llama3.1:8b"
DEBUG = False


def dbg(message):
    if DEBUG:
        print(f"[EVAL3] {message}")


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
        description="Concise feedback on the answer quality, comparing it to the reference answer and evaluating based on the retrieved context"
    )
    accuracy: float = Field(
        description="How factually correct is the answer compared to the reference answer? 1 (wrong. any wrong answer must score 1) to 5 (ideal - perfectly accurate). An acceptable answer would score 3."
    )
    completeness: float = Field(
        description="How complete is the answer in addressing all aspects of the question? 1 (very poor - missing key information) to 5 (ideal - all the information from the reference answer is provided completely). Only answer 5 if ALL information from the reference answer is included."
    )
    relevance: float = Field(
        description="How relevant is the answer to the specific question asked? 1 (very poor - off-topic) to 5 (ideal - directly addresses question and gives no additional information). Only answer 5 if the answer is completely relevant to the question and gives no additional information."
    )


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
    dbg(f"Evaluating retrieval for question: {test.question}")
    retrieved_docs = fetch_context(test.question, model_name=f"ollama/{GENERATION_MODEL}")
    dbg(f"Retrieved docs count: {len(retrieved_docs)}")
    mrr_scores = [calculate_mrr(keyword, retrieved_docs) for keyword in test.keywords]
    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0
    ndcg_scores = [calculate_ndcg(keyword, retrieved_docs, k) for keyword in test.keywords]
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0
    keywords_found = sum(1 for score in mrr_scores if score > 0)
    total_keywords = len(test.keywords)
    keyword_coverage = (keywords_found / total_keywords * 100) if total_keywords > 0 else 0.0
    dbg(
        f"Retrieval metrics -> MRR={avg_mrr:.4f}, nDCG={avg_ndcg:.4f}, coverage={keyword_coverage:.1f}%"
    )
    return RetrievalEval(
        mrr=avg_mrr,
        ndcg=avg_ndcg,
        keywords_found=keywords_found,
        total_keywords=total_keywords,
        keyword_coverage=keyword_coverage,
    )


def evaluate_answer(test: TestQuestion) -> tuple[AnswerEval, str, list]:
    """Evaluate answer quality using LLM-as-a-judge."""
    dbg(f"Evaluating answer for question: {test.question}")
    dbg(f"Calling generation model: {GENERATION_MODEL}")
    generated_answer, retrieved_docs = answer_question(
        test.question, model_name=f"ollama/{GENERATION_MODEL}"
    )
    dbg(f"Generated answer length: {len(generated_answer)} chars")

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

    dbg(f"Calling judge model: {JUDGE_MODEL}")
    judge_llm = ChatOllama(model=JUDGE_MODEL, temperature=0)
    structured_judge = judge_llm.with_structured_output(AnswerEval)
    lc_messages = [
        SystemMessage(content=judge_messages[0]["content"]),
        HumanMessage(content=judge_messages[1]["content"]),
    ]
    answer_eval = structured_judge.invoke(lc_messages)
    dbg(
        f"Answer metrics -> accuracy={answer_eval.accuracy:.2f}, completeness={answer_eval.completeness:.2f}, relevance={answer_eval.relevance:.2f}"
    )
    return answer_eval, generated_answer, retrieved_docs


def evaluate_all_retrieval():
    """Evaluate all retrieval tests."""
    tests = load_tests()
    total_tests = len(tests)
    dbg(f"Running retrieval evaluation for {total_tests} tests")
    for index, test in enumerate(tests):
        result = evaluate_retrieval(test)
        progress = (index + 1) / total_tests
        yield test, result, progress


def evaluate_all_answers():
    """Evaluate all answers to tests."""
    tests = load_tests()
    total_tests = len(tests)
    dbg(f"Running answer evaluation for {total_tests} tests")
    for index, test in enumerate(tests):
        result = evaluate_answer(test)[0]
        progress = (index + 1) / total_tests
        yield test, result, progress


def run_cli_evaluation(test_number: int):
    """Run evaluation for a specific test row number."""
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
    print(f"\nRetrieved docs count: {len(retrieved_docs)}")
    print(f"\nFeedback:\n{answer_result.feedback}")
    print("\nScores:")
    print(f"  Accuracy: {answer_result.accuracy:.2f}/5")
    print(f"  Completeness: {answer_result.completeness:.2f}/5")
    print(f"  Relevance: {answer_result.relevance:.2f}/5")
    print(f"\n{'=' * 80}\n")


def main():
    """CLI to evaluate a specific test by row number."""
    if len(sys.argv) != 2:
        print("Usage: python -m evaluation.eval3 <test_row_number>")
        sys.exit(1)
    try:
        test_number = int(sys.argv[1])
    except ValueError:
        print("Error: test_row_number must be an integer")
        sys.exit(1)
    run_cli_evaluation(test_number)


if __name__ == "__main__":
    main()
