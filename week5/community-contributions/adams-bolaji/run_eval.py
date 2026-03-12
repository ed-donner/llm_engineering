"""
Beat the Numbers: Run evaluation for improved RAG and compare to baseline.

Compares:
- Baseline: standard implementation.answer (simple retrieval, k=10)
- Improved: adams-bolaji answer (query rewrite, over-fetch 20, rerank, top 10)

Run from week5 directory:
  cd week5 && uv run python community-contributions/adams-bolaji/run_eval.py

Or from repo root:
  cd llm_engineering && PYTHONPATH=week5 uv run python week5/community-contributions/adams-bolaji/run_eval.py

Use --improved-only to skip baseline (faster, fewer API calls):
  cd week5 && uv run python community-contributions/adams-bolaji/run_eval.py --improved-only
"""
import argparse
import sys
from pathlib import Path
from collections import defaultdict

WEEK5 = Path(__file__).resolve().parent.parent.parent
ADAMS_BOLAJI = Path(__file__).resolve().parent
sys.path.insert(0, str(WEEK5))
sys.path.insert(0, str(ADAMS_BOLAJI))


def run_eval_with_module(description: str, answer_module):
    """Run full retrieval and answer evaluation using the given answer module."""
    import evaluation.eval as eval_mod

    eval_mod.fetch_context = answer_module.fetch_context
    eval_mod.answer_question = answer_module.answer_question

    # Retrieval
    total_mrr = 0.0
    total_ndcg = 0.0
    total_cov = 0.0
    n = 0
    for test, result, _ in eval_mod.evaluate_all_retrieval():
        n += 1
        total_mrr += result.mrr
        total_ndcg += result.ndcg
        total_cov += result.keyword_coverage

    avg_mrr = total_mrr / n if n else 0
    avg_ndcg = total_ndcg / n if n else 0
    avg_cov = total_cov / n if n else 0

    # Answer
    total_acc = 0.0
    total_comp = 0.0
    total_rel = 0.0
    n_ans = 0
    for test, result, _ in eval_mod.evaluate_all_answers():
        n_ans += 1
        total_acc += result.accuracy
        total_comp += result.completeness
        total_rel += result.relevance

    avg_acc = total_acc / n_ans if n_ans else 0
    avg_comp = total_comp / n_ans if n_ans else 0
    avg_rel = total_rel / n_ans if n_ans else 0

    return {
        "description": description,
        "mrr": avg_mrr,
        "ndcg": avg_ndcg,
        "keyword_coverage": avg_cov,
        "accuracy": avg_acc,
        "completeness": avg_comp,
        "relevance": avg_rel,
        "n": n,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--improved-only", action="store_true", help="Skip baseline, run improved only")
    args = parser.parse_args()

    print("=" * 60)
    print("Beat the Numbers: RAG Evaluation Comparison")
    print("=" * 60)

    baseline_scores = None

    if not args.improved_only:
        # 1. Baseline
        print("\n[1/2] Running BASELINE (implementation.answer)...")
        from implementation import answer as baseline

        baseline_scores = run_eval_with_module("Baseline", baseline)
    print(f"  MRR: {baseline_scores['mrr']:.4f} | nDCG: {baseline_scores['ndcg']:.4f} | "
          f"Coverage: {baseline_scores['keyword_coverage']:.1f}%")
    print(f"  Accuracy: {baseline_scores['accuracy']:.2f}/5 | Completeness: {baseline_scores['completeness']:.2f}/5 | "
          f"Relevance: {baseline_scores['relevance']:.2f}/5")

    # 2. Improved (adams-bolaji)
    step = "2/2" if not args.improved_only else "1/1"
    print(f"\n[{step}] Running IMPROVED (adams-bolaji: query rewrite + rerank)...")
    import answer as improved  # from adams-bolaji/ (on sys.path)

    improved_scores = run_eval_with_module("Improved", improved)
    print(f"  MRR: {improved_scores['mrr']:.4f} | nDCG: {improved_scores['ndcg']:.4f} | "
          f"Coverage: {improved_scores['keyword_coverage']:.1f}%")
    print(f"  Accuracy: {improved_scores['accuracy']:.2f}/5 | Completeness: {improved_scores['completeness']:.2f}/5 | "
          f"Relevance: {improved_scores['relevance']:.2f}/5")

    # 3. Comparison (if baseline was run)
    if baseline_scores:
        print("\n" + "=" * 60)
        print("COMPARISON (Improved vs Baseline)")
        print("=" * 60)

        def delta(before, after):
            diff = after - before
            sign = "+" if diff >= 0 else ""
            return f"{sign}{diff:.4f}"

        print(f"  MRR:              {delta(baseline_scores['mrr'], improved_scores['mrr'])}")
        print(f"  nDCG:             {delta(baseline_scores['ndcg'], improved_scores['ndcg'])}")
        print(f"  Keyword coverage: {delta(baseline_scores['keyword_coverage'], improved_scores['keyword_coverage'])}%")
        print(f"  Accuracy:         {delta(baseline_scores['accuracy'], improved_scores['accuracy'])}/5")
        print(f"  Completeness:     {delta(baseline_scores['completeness'], improved_scores['completeness'])}/5")
        print(f"  Relevance:        {delta(baseline_scores['relevance'], improved_scores['relevance'])}/5")

        # Summary
        gains = []
        if improved_scores["mrr"] > baseline_scores["mrr"]:
            gains.append("MRR")
        if improved_scores["ndcg"] > baseline_scores["ndcg"]:
            gains.append("nDCG")
        if improved_scores["keyword_coverage"] > baseline_scores["keyword_coverage"]:
            gains.append("coverage")
        if improved_scores["accuracy"] > baseline_scores["accuracy"]:
            gains.append("accuracy")
        if improved_scores["completeness"] > baseline_scores["completeness"]:
            gains.append("completeness")
        if improved_scores["relevance"] > baseline_scores["relevance"]:
            gains.append("relevance")

        if gains:
            print(f"\n  Improved on: {', '.join(gains)}")
        else:
            print("\n  No metric improved (baseline may use different embeddings/DB).")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
