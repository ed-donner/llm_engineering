import os
import sys
import math
from pydantic import BaseModel, Field
from litellm import completion
from dotenv import load_dotenv

# Set sys.path to find 'evaluation' and 'implementation'
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_dir = os.path.dirname(parent_dir)
sys.path.append(parent_dir)
sys.path.append(root_dir)

# Load environment variables from project root
dotenv_path = os.path.join(root_dir, ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)

from evaluation.test import TestQuestion, load_tests

# Dynamic import based on command line argument 'pro'
use_pro = any(arg.lower() == "pro" for arg in sys.argv)
if use_pro:
    from pro_implementation.answer import answer_question, fetch_context
    print("[EVAL] Using PRO implementation")
else:
    from implementation.answer import answer_question, fetch_context
    print("[EVAL] Using Basic implementation")

MODEL = "openai/gpt-4o-mini"
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
        dcg += relevances[i] / math.log2(i + 2)  # i+2 because rank starts at 1
    return dcg


def calculate_ndcg(keyword: str, retrieved_docs: list, k: int = 10) -> float:
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


def evaluate_retrieval(test: TestQuestion, k: int = 10) -> RetrievalEval:
    """
    Evaluate retrieval performance for a test question.

    Args:
        test: TestQuestion object containing question and keywords
        k: Number of top documents to retrieve (default 10)

    Returns:
        RetrievalEval object with MRR, nDCG, and keyword coverage metrics
    """
    # Retrieve documents using shared answer module
    retrieved_docs = fetch_context(test.question)

    # Calculate MRR (average across all keywords)
    mrr_scores = [calculate_mrr(keyword, retrieved_docs) for keyword in test.keywords]
    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0

    # Calculate nDCG (average across all keywords)
    ndcg_scores = [calculate_ndcg(keyword, retrieved_docs, k) for keyword in test.keywords]
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0

    # Calculate keyword coverage
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
    """
    Evaluate answer quality using LLM-as-a-judge (async).

    Args:
        test: TestQuestion object containing question and reference answer

    Returns:
        Tuple of (AnswerEval object, generated_answer string, retrieved_docs list)
    """
    # Get RAG response using shared answer module
    generated_answer, retrieved_docs = answer_question(test.question)

    # LLM judge prompt
    judge_messages = [
        {
            "role": "system",
            "content": "Compare generated and reference answers.",
        },
        {
            "role": "user",
            "content": f"""Q: {test.question}
Gen: {generated_answer}
Ref: {test.reference_answer}
Evaluate on Accuracy, Completeness, Relevance (1-5). If Gen is wrong, Accuracy is 1. Keep feedback under 5 words.""",
        },
    ]

    # Call LLM judge with structured outputs (async)
    judge_response = completion(
        model=MODEL,
        messages=judge_messages,
        response_format=AnswerEval,
        api_base="https://openrouter.ai/api/v1",
        max_tokens=50
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

    # Retrieval Evaluation
    print(f"\n{'=' * 80}")
    print("Retrieval Evaluation")
    print(f"{'=' * 80}")

    retrieval_result = evaluate_retrieval(test)

    print(f"MRR: {retrieval_result.mrr:.4f}")
    print(f"nDCG: {retrieval_result.ndcg:.4f}")
    print(f"Keywords Found: {retrieval_result.keywords_found}/{retrieval_result.total_keywords}")
    print(f"Keyword Coverage: {retrieval_result.keyword_coverage:.1f}%")

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


def run_all_cli_evaluation(limit: int = 5):
    """Run retrieval evaluation for all 150 tests, and answer evaluation for first N tests."""
    print(f"\n{'=' * 80}")
    print(f"RUNNING COMPLETE EVALUATION (Retrieval: all 150 tests, Answers: first {limit} tests)")
    print(f"{'=' * 80}")
    
    # 1. Retrieval Evaluation
    print("\nRunning Retrieval Evaluation across all 150 tests...")
    total_mrr = 0.0
    total_ndcg = 0.0
    total_coverage = 0.0
    count = 0
    
    for test, result, progress in evaluate_all_retrieval():
        total_mrr += result.mrr
        total_ndcg += result.ndcg
        total_coverage += result.keyword_coverage
        count += 1
        
    avg_mrr = total_mrr / count if count > 0 else 0.0
    avg_ndcg = total_ndcg / count if count > 0 else 0.0
    avg_coverage = total_coverage / count if count > 0 else 0.0
    
    print(f"\nRetrieval Results (averaged over {count} tests):")
    print(f"  Mean Reciprocal Rank (MRR): {avg_mrr:.4f}")
    print(f"  nDCG: {avg_ndcg:.4f}")
    print(f"  Keyword Coverage: {avg_coverage:.1f}%")
    
    # 2. Answer Evaluation
    print(f"\nRunning Answer Evaluation for first {limit} tests...")
    tests = load_tests()
    total_acc = 0.0
    total_comp = 0.0
    total_rel = 0.0
    ans_count = 0
    
    for i in range(min(limit, len(tests))):
        test = tests[i]
        try:
            result, generated, _ = evaluate_answer(test)
            total_acc += result.accuracy
            total_comp += result.completeness
            total_rel += result.relevance
            ans_count += 1
            print(f"  Test #{i}: Acc={result.accuracy:.1f}, Comp={result.completeness:.1f}, Rel={result.relevance:.1f}")
        except Exception as e:
            print(f"  Test #{i} failed: {e}")
            
    avg_acc = total_acc / ans_count if ans_count > 0 else 0.0
    avg_comp = total_comp / ans_count if ans_count > 0 else 0.0
    avg_rel = total_rel / ans_count if ans_count > 0 else 0.0
    
    print(f"\nAnswer Quality Results (averaged over {ans_count} tests):")
    print(f"  Accuracy: {avg_acc:.2f}/5")
    print(f"  Completeness: {avg_comp:.2f}/5")
    print(f"  Relevance: {avg_rel:.2f}/5")
    print(f"\n{'=' * 80}\n")


def main():
    """CLI to evaluate a specific test by row number or 'all'."""
    args = [arg for arg in sys.argv[1:] if arg.lower() != "pro"]
    if len(args) != 1:
        print("Usage: uv run eval.py <test_row_number | all> [pro]")
        sys.exit(1)

    arg = args[0]
    if arg.lower() == "all":
        run_all_cli_evaluation(limit=5)
    else:
        try:
            test_number = int(arg)
        except ValueError:
            print("Error: argument must be an integer or 'all'")
            sys.exit(1)
        run_cli_evaluation(test_number)


if __name__ == "__main__":
    main()
