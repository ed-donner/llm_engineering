import sys
import math
from pydantic import BaseModel, Field
from litellm import completion
from dotenv import load_dotenv

from evaluation.test import TestQuestion, load_tests
from implementation.answer import (
    answer_question,
    fetch_context,
    fetch_context_fast,
    get_vector_store,
    build_bm25_index,
)

load_dotenv(override=True)

MODEL = "gpt-4.1-nano"


# Reuse one cloud vector store connection
vector_store = get_vector_store(use_cloud=True)
bm25_index = build_bm25_index(vector_store)


class RetrievalEval(BaseModel):
    mrr: float
    ndcg: float
    keywords_found: int
    total_keywords: int
    keyword_coverage: float


class AnswerEval(BaseModel):
    feedback: str
    accuracy: float
    completeness: float
    relevance: float


def calculate_mrr(keyword: str, retrieved_docs: list) -> float:
    keyword_lower = keyword.lower()

    for rank, doc in enumerate(retrieved_docs, start=1):
        if keyword_lower in doc.page_content.lower():
            return 1.0 / rank

    return 0.0


def calculate_dcg(relevances: list[int], k: int) -> float:
    dcg = 0.0

    for i in range(min(k, len(relevances))):
        dcg += relevances[i] / math.log2(i + 2)

    return dcg


def calculate_ndcg(keyword: str, retrieved_docs: list, k: int = 10) -> float:
    keyword_lower = keyword.lower()

    relevances = [
        1 if keyword_lower in doc.page_content.lower() else 0
        for doc in retrieved_docs[:k]
    ]

    dcg = calculate_dcg(relevances, k)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = calculate_dcg(ideal_relevances, k)

    return dcg / idcg if idcg > 0 else 0.0


def evaluate_retrieval(
    test: TestQuestion,
    k: int = 10,
    mode: str = "fast",
) -> RetrievalEval:
    if mode == "fast":
        
        retrieved_docs = fetch_context_fast(
            vector_store=vector_store,
            question=test.question,
            k=k,
            bm25_index=bm25_index
        )
    else:
        retrieved_docs = fetch_context(
            vector_store=vector_store,
            question=test.question,
            history=[],
            bm25_index=bm25_index,
        )

    mrr_scores = [
        calculate_mrr(keyword, retrieved_docs)
        for keyword in test.keywords
    ]

    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0

    ndcg_scores = [
        calculate_ndcg(keyword, retrieved_docs, k)
        for keyword in test.keywords
    ]

    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0

    keywords_found = sum(1 for score in mrr_scores if score > 0)
    total_keywords = len(test.keywords)

    keyword_coverage = (
        keywords_found / total_keywords * 100
        if total_keywords > 0
        else 0.0
    )

    return RetrievalEval(
        mrr=avg_mrr,
        ndcg=avg_ndcg,
        keywords_found=keywords_found,
        total_keywords=total_keywords,
        keyword_coverage=keyword_coverage,
    )


def evaluate_answer(
    test: TestQuestion,
    mode: str = "fast",
) -> tuple[AnswerEval, str, list]:
    generated_answer, retrieved_docs = answer_question(
        question=test.question,
        vector_store=vector_store,
        use_cloud=True,
        mode=mode,
    )

    judge_messages = [
        {
            "role": "system",
            "content": (
                "You are an expert evaluator assessing RAG answer quality. "
                "Compare the generated answer to the reference answer. "
                "Only give 5/5 for perfect answers. "
                "If the answer is wrong, accuracy must be 1."
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

Evaluate:
1. Accuracy: factual correctness vs reference answer.
2. Completeness: whether all key information is included.
3. Relevance: whether it directly answers the question without unnecessary content.

Return structured scores from 1 to 5 and concise feedback.""",
        },
    ]

    judge_response = completion(
        model=MODEL,
        messages=judge_messages,
        response_format=AnswerEval,
    )

    answer_eval = AnswerEval.model_validate_json(
        judge_response.choices[0].message.content
    )

    return answer_eval, generated_answer, retrieved_docs


def evaluate_all_retrieval(mode: str = "fast"):
    tests = load_tests()
    total_tests = len(tests)

    for index, test in enumerate(tests):
        result = evaluate_retrieval(test, mode=mode)
        progress = (index + 1) / total_tests
        yield test, result, progress


def evaluate_all_answers(mode: str = "fast"):
    tests = load_tests()
    total_tests = len(tests)

    for index, test in enumerate(tests):
        result = evaluate_answer(test, mode=mode)[0]
        progress = (index + 1) / total_tests
        yield test, result, progress


def print_retrieved_docs(retrieved_docs: list):
    print("\nRetrieved chunks:\n")

    for i, doc in enumerate(retrieved_docs, start=1):
        meta = doc.metadata

        print(f"{i}. {meta.get('source', '')}")
        print(f"   Section: {meta.get('section_title', '')}")
        print(f"   Topic: {meta.get('topic', '')}")
        print(f"   Pages: {meta.get('page_start', '?')}-{meta.get('page_end', '?')}")
        print(f"   Preview: {doc.page_content[:250]}...")
        print()


def run_cli_evaluation(test_number: int, mode: str = "fast"):
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
    print(f"Mode: {mode}")

    print(f"\n{'=' * 80}")
    print("Retrieval Evaluation")
    print(f"{'=' * 80}")

    retrieval_result = evaluate_retrieval(test, mode=mode)

    print(f"MRR: {retrieval_result.mrr:.4f}")
    print(f"nDCG: {retrieval_result.ndcg:.4f}")
    print(f"Keywords Found: {retrieval_result.keywords_found}/{retrieval_result.total_keywords}")
    print(f"Keyword Coverage: {retrieval_result.keyword_coverage:.1f}%")

    print(f"\n{'=' * 80}")
    print("Answer Evaluation")
    print(f"{'=' * 80}")

    answer_result, generated_answer, retrieved_docs = evaluate_answer(
        test,
        mode=mode,
    )

    print(f"\nGenerated Answer:\n{generated_answer}")
    print(f"\nFeedback:\n{answer_result.feedback}")
    print("\nScores:")
    print(f"  Accuracy: {answer_result.accuracy:.2f}/5")
    print(f"  Completeness: {answer_result.completeness:.2f}/5")
    print(f"  Relevance: {answer_result.relevance:.2f}/5")

    print_retrieved_docs(retrieved_docs)

    print(f"\n{'=' * 80}\n")


def main():
    if len(sys.argv) not in [2, 3]:
        print("Usage: uv run evaluate.py <test_row_number> [fast|accurate]")
        sys.exit(1)

    try:
        test_number = int(sys.argv[1])
    except ValueError:
        print("Error: test_row_number must be an integer")
        sys.exit(1)

    mode = sys.argv[2] if len(sys.argv) == 3 else "fast"

    if mode not in ["fast", "accurate"]:
        print("Error: mode must be 'fast' or 'accurate'")
        sys.exit(1)

    run_cli_evaluation(test_number, mode=mode)


if __name__ == "__main__":
    main()