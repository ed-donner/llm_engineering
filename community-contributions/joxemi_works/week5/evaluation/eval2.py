"""
ULTRA DUMMIE DESCRIPTION
------------------------
What this file does:
- Evaluates your RAG system in two parts:
  1) Retrieval quality (MRR, nDCG, keyword coverage)
  2) Answer quality (LLM-as-a-judge vs reference answer)

Internal steps:
1) Loads tests from test2.py.
2) Calls answer2.py retrieval and answer functions.
3) Computes retrieval metrics for each test.
4) Asks a judge model to score generated answers.
5) Prints results in CLI for one selected test.

Key logic:
- Retrieval and generation are evaluated separately.
- Debug traces help you inspect each step and metric.
"""

import sys  # Imports sys for CLI arguments and exits.
import math  # Imports math utilities for ranking metrics.
from pydantic import BaseModel, Field  # Imports Pydantic for structured evaluation outputs.
from langchain_ollama import ChatOllama  # Imports Ollama chat model for local LLM-as-a-judge scoring.
from langchain_core.messages import SystemMessage, HumanMessage  # Imports message types for judge prompts.
from dotenv import load_dotenv  # Imports .env loader for API credentials.

from evaluation.test2 import TestQuestion, load_tests  # Imports test model and loader from test2 module.
from implementation.answer2 import answer_question, fetch_context  # Imports RAG answer and retrieval functions from answer2.


load_dotenv(override=True)  # Loads environment variables and allows overwrite.

GENERATION_MODEL = "phi3.5:latest"  # Defines local Ollama model used to generate RAG answers during evaluation.
JUDGE_MODEL = "llama3.1:8b"  # Defines local Ollama model used as judge for answer evaluation.
DEBUG = True  # Enables or disables debug traces for this module.


def dbg(message):  # Defines helper to print logs only when DEBUG is active.
    if DEBUG:  # Checks debug flag.
        print(f"[EVAL] {message}")  # Prints log line with module prefix.


class RetrievalEval(BaseModel):  # Defines retrieval metrics output schema.
    """Evaluation metrics for retrieval performance."""  # Describes retrieval metrics container.

    mrr: float = Field(description="Mean Reciprocal Rank - average across all keywords")  # Stores average MRR across expected keywords.
    ndcg: float = Field(description="Normalized Discounted Cumulative Gain (binary relevance)")  # Stores average nDCG score.
    keywords_found: int = Field(description="Number of keywords found in top-k results")  # Stores number of keywords found at least once.
    total_keywords: int = Field(description="Total number of keywords to find")  # Stores total expected keywords.
    keyword_coverage: float = Field(description="Percentage of keywords found")  # Stores percentage coverage of expected keywords.


class AnswerEval(BaseModel):  # Defines answer-quality scoring schema produced by judge model.
    """LLM-as-a-judge evaluation of answer quality."""  # Describes answer evaluation container.

    feedback: str = Field(  # Defines textual qualitative feedback field.
        description="Concise feedback on the answer quality, comparing it to the reference answer and evaluating based on the retrieved context"  # Documents feedback meaning.
    )  # Closes feedback field definition.
    accuracy: float = Field(  # Defines factual correctness score field.
        description="How factually correct is the answer compared to the reference answer? 1 (wrong. any wrong answer must score 1) to 5 (ideal - perfectly accurate). An acceptable answer would score 3."  # Documents accuracy scoring rubric.
    )  # Closes accuracy field definition.
    completeness: float = Field(  # Defines completeness score field.
        description="How complete is the answer in addressing all aspects of the question? 1 (very poor - missing key information) to 5 (ideal - all the information from the reference answer is provided completely). Only answer 5 if ALL information from the reference answer is included."  # Documents completeness scoring rubric.
    )  # Closes completeness field definition.
    relevance: float = Field(  # Defines relevance score field.
        description="How relevant is the answer to the specific question asked? 1 (very poor - off-topic) to 5 (ideal - directly addresses question and gives no additional information). Only answer 5 if the answer is completely relevant to the question and gives no additional information."  # Documents relevance scoring rubric.
    )  # Closes relevance field definition.


def calculate_mrr(keyword: str, retrieved_docs: list) -> float:  # Defines reciprocal rank for one keyword.
    """Calculate reciprocal rank for a single keyword (case-insensitive)."""  # Documents MRR helper behavior.
    keyword_lower = keyword.lower()  # Normalizes keyword for case-insensitive matching.
    for rank, doc in enumerate(retrieved_docs, start=1):  # Iterates retrieved documents with rank starting at 1.
        if keyword_lower in doc.page_content.lower():  # Checks if keyword appears in current document text.
            return 1.0 / rank  # Returns reciprocal rank of first match.
    return 0.0  # Returns zero when keyword is not found in retrieved docs.


def calculate_dcg(relevances: list[int], k: int) -> float:  # Defines DCG computation helper.
    """Calculate Discounted Cumulative Gain."""  # Documents DCG helper behavior.
    dcg = 0.0  # Initializes DCG accumulator.
    for i in range(min(k, len(relevances))):  # Iterates up to top-k relevance entries.
        dcg += relevances[i] / math.log2(i + 2)  # Adds discounted relevance at position i.
    return dcg  # Returns final DCG value.


def calculate_ndcg(keyword: str, retrieved_docs: list, k: int = 10) -> float:  # Defines nDCG computation for one keyword.
    """Calculate nDCG for a single keyword (binary relevance, case-insensitive)."""  # Documents nDCG helper behavior.
    keyword_lower = keyword.lower()  # Normalizes keyword for case-insensitive matching.
    relevances = [  # Builds binary relevance list for top-k docs.
        1 if keyword_lower in doc.page_content.lower() else 0 for doc in retrieved_docs[:k]
    ]  # Closes binary relevance list.
    dcg = calculate_dcg(relevances, k)  # Computes DCG for observed ranking.
    ideal_relevances = sorted(relevances, reverse=True)  # Creates ideal ranking by sorting relevances descending.
    idcg = calculate_dcg(ideal_relevances, k)  # Computes ideal DCG baseline.
    return dcg / idcg if idcg > 0 else 0.0  # Returns normalized DCG with zero-safe division.


def evaluate_retrieval(test: TestQuestion, k: int = 10) -> RetrievalEval:  # Defines retrieval evaluation for one test case.
    """Evaluate retrieval performance for a test question."""  # Documents retrieval evaluation behavior.
    dbg(f"Evaluating retrieval for question: {test.question}")  # Traces current retrieval test question.
    retrieved_docs = fetch_context(test.question)  # Retrieves docs using shared answer2 retrieval logic.
    dbg(f"Retrieved docs count: {len(retrieved_docs)}")  # Traces number of retrieved docs.
    mrr_scores = [calculate_mrr(keyword, retrieved_docs) for keyword in test.keywords]  # Computes one MRR score per keyword.
    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0  # Averages MRR scores safely.
    ndcg_scores = [calculate_ndcg(keyword, retrieved_docs, k) for keyword in test.keywords]  # Computes one nDCG score per keyword.
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0  # Averages nDCG scores safely.
    keywords_found = sum(1 for score in mrr_scores if score > 0)  # Counts keywords that appeared in retrieval.
    total_keywords = len(test.keywords)  # Gets total expected keywords.
    keyword_coverage = (keywords_found / total_keywords * 100) if total_keywords > 0 else 0.0  # Computes keyword coverage percentage.
    dbg(f"Retrieval metrics -> MRR={avg_mrr:.4f}, nDCG={avg_ndcg:.4f}, coverage={keyword_coverage:.1f}%")  # Traces retrieval metrics summary.
    return RetrievalEval(  # Builds structured retrieval evaluation result.
        mrr=avg_mrr,  # Sets average MRR.
        ndcg=avg_ndcg,  # Sets average nDCG.
        keywords_found=keywords_found,  # Sets count of found keywords.
        total_keywords=total_keywords,  # Sets total keywords count.
        keyword_coverage=keyword_coverage,  # Sets keyword coverage percentage.
    )  # Returns RetrievalEval object.


def evaluate_answer(test: TestQuestion) -> tuple[AnswerEval, str, list]:  # Defines answer-quality evaluation for one test case.
    """Evaluate answer quality using LLM-as-a-judge."""  # Documents answer evaluation behavior.
    dbg(f"Evaluating answer for question: {test.question}")  # Traces current answer test question.
    dbg(f"Calling generation model: {GENERATION_MODEL}")  # Traces generation model invocation.
    generated_answer, retrieved_docs = answer_question(test.question, model_name=GENERATION_MODEL)  # Gets RAG answer and retrieved docs from answer2 using generation-model override.
    dbg(f"Generated answer length: {len(generated_answer)} chars")  # Traces generated answer size.
    judge_messages = [  # Builds messages for judge model prompt.
        {  # Defines judge system message.
            "role": "system",  # Sets role as system.
            "content": "You are an expert evaluator assessing the quality of answers. Evaluate the generated answer by comparing it to the reference answer. Only give 5/5 scores for perfect answers.",  # Sets judge behavior and strict scoring policy.
        },  # Closes system message dict.
        {  # Defines judge user message.
            "role": "user",  # Sets role as user.
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

Provide detailed feedback and scores from 1 (very poor) to 5 (ideal) for each dimension. If the answer is wrong, then the accuracy score must be 1.""",  # Injects test question, generated answer, and reference answer into judge instruction.
        },  # Closes user message dict.
    ]  # Closes judge messages list.
    dbg(f"Calling judge model: {JUDGE_MODEL}")  # Traces judge model invocation.
    judge_llm = ChatOllama(model=JUDGE_MODEL, temperature=0)  # Initializes local Ollama judge model with deterministic behavior.
    structured_judge = judge_llm.with_structured_output(AnswerEval)  # Wraps model to return validated AnswerEval schema.
    lc_messages = [  # Converts judge prompt into LangChain message objects.
        SystemMessage(content=judge_messages[0]["content"]),  # Adds system instruction for judge behavior.
        HumanMessage(content=judge_messages[1]["content"]),  # Adds user payload with question, generated answer, and reference.
    ]  # Closes message list for structured judge call.
    answer_eval = structured_judge.invoke(lc_messages)  # Invokes judge and gets structured AnswerEval output.
    dbg(  # Traces final answer metrics.
        f"Answer metrics -> accuracy={answer_eval.accuracy:.2f}, completeness={answer_eval.completeness:.2f}, relevance={answer_eval.relevance:.2f}"
    )  # Closes debug line.
    return answer_eval, generated_answer, retrieved_docs  # Returns structured answer evaluation plus raw answer/context.


def evaluate_all_retrieval():  # Defines generator to evaluate retrieval for all tests.
    """Evaluate all retrieval tests."""  # Documents retrieval batch evaluation behavior.
    tests = load_tests()  # Loads all tests from JSONL.
    total_tests = len(tests)  # Stores total test count for progress tracking.
    dbg(f"Running retrieval evaluation for {total_tests} tests")  # Traces retrieval batch size.
    for index, test in enumerate(tests):  # Iterates all tests with index.
        result = evaluate_retrieval(test)  # Evaluates retrieval for current test.
        progress = (index + 1) / total_tests  # Computes progress ratio in [0,1].
        yield test, result, progress  # Yields incremental result for caller.


def evaluate_all_answers():  # Defines generator to evaluate answers for all tests.
    """Evaluate all answers to tests."""  # Documents answer batch evaluation behavior.
    tests = load_tests()  # Loads all tests from JSONL.
    total_tests = len(tests)  # Stores total test count for progress tracking.
    dbg(f"Running answer evaluation for {total_tests} tests")  # Traces answer batch size.
    for index, test in enumerate(tests):  # Iterates all tests with index.
        result = evaluate_answer(test)[0]  # Evaluates answer and keeps only AnswerEval object.
        progress = (index + 1) / total_tests  # Computes progress ratio in [0,1].
        yield test, result, progress  # Yields incremental result for caller.


def run_cli_evaluation(test_number: int):  # Defines CLI helper to evaluate one selected test row.
    """Run evaluation for a specific test row number."""  # Documents single-test CLI behavior.
    tests = load_tests()  # Loads all tests from JSONL.
    if test_number < 0 or test_number >= len(tests):  # Validates test index bounds.
        print(f"Error: test_row_number must be between 0 and {len(tests) - 1}")  # Prints user-facing index error.
        sys.exit(1)  # Exits process with error code.
    test = tests[test_number]  # Selects requested test.
    print(f"\n{'=' * 80}")  # Prints separator line.
    print(f"Test #{test_number}")  # Prints selected test index.
    print(f"{'=' * 80}")  # Prints separator line.
    print(f"Question: {test.question}")  # Prints test question.
    print(f"Keywords: {test.keywords}")  # Prints expected keywords.
    print(f"Category: {test.category}")  # Prints test category.
    print(f"Reference Answer: {test.reference_answer}")  # Prints reference answer.
    print(f"\n{'=' * 80}")  # Prints separator line.
    print("Retrieval Evaluation")  # Prints retrieval section title.
    print(f"{'=' * 80}")  # Prints separator line.
    retrieval_result = evaluate_retrieval(test)  # Runs retrieval evaluation for selected test.
    print(f"MRR: {retrieval_result.mrr:.4f}")  # Prints retrieval MRR metric.
    print(f"nDCG: {retrieval_result.ndcg:.4f}")  # Prints retrieval nDCG metric.
    print(f"Keywords Found: {retrieval_result.keywords_found}/{retrieval_result.total_keywords}")  # Prints found/total keywords.
    print(f"Keyword Coverage: {retrieval_result.keyword_coverage:.1f}%")  # Prints keyword coverage percentage.
    print(f"\n{'=' * 80}")  # Prints separator line.
    print("Answer Evaluation")  # Prints answer section title.
    print(f"{'=' * 80}")  # Prints separator line.
    answer_result, generated_answer, retrieved_docs = evaluate_answer(test)  # Runs answer evaluation for selected test.
    print(f"\nGenerated Answer:\n{generated_answer}")  # Prints generated answer text.
    print(f"\nRetrieved docs count: {len(retrieved_docs)}")  # Prints number of retrieved docs for transparency.
    print(f"\nFeedback:\n{answer_result.feedback}")  # Prints judge feedback.
    print("\nScores:")  # Prints scores section title.
    print(f"  Accuracy: {answer_result.accuracy:.2f}/5")  # Prints accuracy score.
    print(f"  Completeness: {answer_result.completeness:.2f}/5")  # Prints completeness score.
    print(f"  Relevance: {answer_result.relevance:.2f}/5")  # Prints relevance score.
    print(f"\n{'=' * 80}\n")  # Prints final separator line.


def main():  # Defines CLI entrypoint function.
    """CLI to evaluate a specific test by row number."""  # Documents main CLI behavior.
    if len(sys.argv) != 2:  # Validates required CLI argument count.
        print("Usage: python -m evaluation.eval2 <test_row_number>")  # Prints expected CLI usage.
        sys.exit(1)  # Exits process with error code.
    try:  # Starts safe parsing block for test row argument.
        test_number = int(sys.argv[1])  # Converts CLI arg into integer row index.
    except ValueError:  # Catches invalid non-integer input.
        print("Error: test_row_number must be an integer")  # Prints user-facing type error.
        sys.exit(1)  # Exits process with error code.
    run_cli_evaluation(test_number)  # Runs evaluation for selected row number.


if __name__ == "__main__":  # Runs main only when file is executed directly.
    main()  # Launches CLI flow.
