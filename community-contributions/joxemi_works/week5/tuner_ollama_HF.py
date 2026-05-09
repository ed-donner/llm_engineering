import itertools
import json
from collections import defaultdict
from pathlib import Path
import sys
import random
import math

# Allow direct execution from evaluation/ with: uv run tuner_ollama_HF.py
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.eval_ollama_HF import evaluate_answer, evaluate_retrieval
from evaluation.test_ollama_HF import load_tests
import pro_implementation.answer_ollama_HF as answer_ollama_HF


# Weighted objective for RAG tuning.
# Retrieval and answer metrics are combined into a single score in [0,1].
WEIGHTS = {
    "mrr": 0.10,
    "ndcg": 0.08,
    "coverage": 0.07,
    "accuracy": 0.5,
    "completeness": 0.15,
    "relevance": 0.1,
}

# Candidate grid to explore.
# The tuner will evaluate all retrieval_k x final_k combinations.
RETRIEVAL_GRID = [10,12,14]
FINAL_GRID = [5,6,7]

RESULTS_DIR = Path(__file__).parent / "results_ollama_HF"
RESULTS_FILE = RESULTS_DIR / "tuning_results.jsonl"
# If MAX_TESTS is None, the fold size is driven by proportional sampling.
MAX_TESTS = None
RANDOM_SEED = 42
N_FOLDS = 2
PROGRESS_EVERY = 10
PRINT_EACH_TEST = True
PRINT_ANSWER_PREVIEW = True
# Proportional sampling controls.
SAMPLE_RATE = 0.3
MIN_PER_CATEGORY = 3


def stratified_subset(tests, max_tests: int | None, seed: int):
    """Sample a balanced subset by category with deterministic randomness."""
    by_category = defaultdict(list)
    for t in tests:
        by_category[t.category].append(t)

    categories = sorted(by_category.keys())
    rng = random.Random(seed)
    subset = []
    for cat in categories:
        items = by_category[cat][:]
        rng.shuffle(items)
        # Proportional sampling with a minimum per category.
        proportional_take = int(math.ceil(len(items) * SAMPLE_RATE))
        take = min(len(items), max(MIN_PER_CATEGORY, proportional_take))
        subset.extend(items[:take])

    target_size = max_tests if max_tests is not None else len(subset)

    # If some categories don't have enough examples, fill from remaining pool.
    # This keeps fold size stable while preserving stratification as much as possible.
    if len(subset) < target_size:
        picked_ids = {id(t) for t in subset}
        remaining = [t for t in tests if id(t) not in picked_ids]
        rng.shuffle(remaining)
        subset.extend(remaining[: target_size - len(subset)])

    return subset[:target_size]


def build_folds(max_tests: int | None = MAX_TESTS, n_folds: int = N_FOLDS, seed: int = RANDOM_SEED):
    """Build multiple stratified folds with different seeds for robustness."""
    tests = load_tests()
    return [stratified_subset(tests, max_tests=max_tests, seed=seed + i) for i in range(n_folds)]


def weighted_score(metrics: dict) -> float:
    # Normalize all components to [0,1] before weighting.
    return (
        WEIGHTS["mrr"] * metrics["mrr"]
        + WEIGHTS["ndcg"] * metrics["ndcg"]
        + WEIGHTS["coverage"] * (metrics["coverage"] / 100.0)
        + WEIGHTS["accuracy"] * (metrics["accuracy"] / 5.0)
        + WEIGHTS["completeness"] * (metrics["completeness"] / 5.0)
        + WEIGHTS["relevance"] * (metrics["relevance"] / 5.0)
    )


def evaluate_candidate(
    retrieval_k: int, final_k: int, tests, fold_idx: int | None = None, n_folds: int | None = None
) -> dict:
    # Apply candidate retrieval settings to answer_ollama_HF at runtime.
    answer_ollama_HF.set_retrieval_config(retrieval_k=retrieval_k, final_k=final_k)

    total = {
        "mrr": 0.0,
        "ndcg": 0.0,
        "coverage": 0.0,
        "accuracy": 0.0,
        "completeness": 0.0,
        "relevance": 0.0,
    }

    total_tests = len(tests)
    if fold_idx is not None and n_folds is not None:
        print(f"  Fold {fold_idx}/{n_folds} -> {total_tests} tests")

    # Evaluate each test with both retrieval and answer judges.
    for idx, test in enumerate(tests, start=1):
        r = evaluate_retrieval(test)
        a, generated_answer, _ = evaluate_answer(test)
        total["mrr"] += r.mrr
        total["ndcg"] += r.ndcg
        total["coverage"] += r.keyword_coverage
        total["accuracy"] += a.accuracy
        total["completeness"] += a.completeness
        total["relevance"] += a.relevance
        if PRINT_EACH_TEST:
            question_preview = test.question.strip().replace("\n", " ")
            if len(question_preview) > 120:
                question_preview = question_preview[:117] + "..."
            answer_preview = generated_answer.strip().replace("\n", " ")
            if len(answer_preview) > 160:
                answer_preview = answer_preview[:157] + "..."
            print(
                "    test {idx}/{total_tests} | cat={cat} | q=\"{q}\" | mrr={mrr:.3f} ndcg={ndcg:.3f} cov={cov:.1f}% "
                "acc={acc:.2f} comp={comp:.2f} rel={rel:.2f}".format(
                    idx=idx,
                    total_tests=total_tests,
                    cat=test.category,
                    q=question_preview,
                    mrr=r.mrr,
                    ndcg=r.ndcg,
                    cov=r.keyword_coverage,
                    acc=a.accuracy,
                    comp=a.completeness,
                    rel=a.relevance,
                )
            )
            if PRINT_ANSWER_PREVIEW:
                print(f"      answer=\"{answer_preview}\"")
        if idx % PROGRESS_EVERY == 0 or idx == total_tests:
            if fold_idx is not None and n_folds is not None:
                print(f"    progress: fold {fold_idx}/{n_folds} test {idx}/{total_tests}")
            else:
                print(f"    progress: test {idx}/{total_tests}")

    # Return fold-level averages for this candidate.
    n = max(1, len(tests))
    avg = {k: v / n for k, v in total.items()}
    avg["retrieval_k"] = retrieval_k
    avg["final_k"] = final_k
    avg["score"] = weighted_score(avg)
    avg["loss"] = 1.0 - avg["score"]
    return avg


def evaluate_candidate_folds(retrieval_k: int, final_k: int, folds) -> dict:
    """Evaluate one candidate across folds and average fold scores."""
    fold_results = []
    n_folds = len(folds)
    for fold_idx, tests in enumerate(folds, start=1):
        fold_result = evaluate_candidate(
            retrieval_k, final_k, tests, fold_idx=fold_idx, n_folds=n_folds
        )
        fold_results.append(fold_result)
    n = max(1, len(fold_results))
    keys = ["mrr", "ndcg", "coverage", "accuracy", "completeness", "relevance", "score", "loss"]
    averaged = {k: sum(r[k] for r in fold_results) / n for k in keys}
    averaged["retrieval_k"] = retrieval_k
    averaged["final_k"] = final_k
    averaged["n_folds"] = n
    averaged["max_tests"] = len(folds[0]) if folds else 0
    averaged["sample_rate"] = SAMPLE_RATE
    averaged["min_per_category"] = MIN_PER_CATEGORY
    return averaged


def save_result(result: dict):
    """Append candidate result to a JSONL log for traceability."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=True) + "\n")


def run_tuning():
    """Main tuning loop: evaluate all candidates and keep the best score."""
    folds = build_folds()
    print(f"Tuning set size per fold: {len(folds[0]) if folds else 0} tests")
    print(
        f"Sampling: rate={SAMPLE_RATE:.2f}, min_per_category={MIN_PER_CATEGORY} | Folds: {len(folds)} | Seed: {RANDOM_SEED}"
    )
    print(f"Grid size: {len(RETRIEVAL_GRID) * len(FINAL_GRID)} candidates")

    best = None
    for retrieval_k, final_k in itertools.product(RETRIEVAL_GRID, FINAL_GRID):
        print(f"\nEvaluating candidate RETRIEVAL_K={retrieval_k}, FINAL_K={final_k}")
        result = evaluate_candidate_folds(retrieval_k, final_k, folds)
        save_result(result)
        print(
            "score={score:.4f} | mrr={mrr:.4f} ndcg={ndcg:.4f} cov={coverage:.1f}% "
            "acc={accuracy:.2f} comp={completeness:.2f} rel={relevance:.2f}".format(**result)
        )
        if best is None or result["score"] > best["score"]:
            best = result
            print(
                f"New best -> RETRIEVAL_K={best['retrieval_k']}, FINAL_K={best['final_k']}, score={best['score']:.4f}"
            )

    print("\n=== Best candidate ===")
    print(json.dumps(best, indent=2))


if __name__ == "__main__":
    run_tuning()
