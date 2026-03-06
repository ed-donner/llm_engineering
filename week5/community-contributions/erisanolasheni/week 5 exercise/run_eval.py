"""
Run the official Week 5 evaluation using the improved RAG pipeline.
Patch evaluation.eval to use improved_rag.fetch_context and answer_question, then run retrieval and answer evals.

Run from the week5 directory:
  cd week5 && uv run python "community-contributions/erisanolasheni/week 5 exercise/run_eval.py"

Or from repo root with week5 on PYTHONPATH:
  cd llm_engineering && PYTHONPATH=week5 uv run python week5/community-contributions/erisanolasheni/week\ 5\ exercise/run_eval.py
"""
import sys
from pathlib import Path
from collections import defaultdict

WEEK5 = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WEEK5))

import improved_rag
import evaluation.eval as eval_mod

eval_mod.fetch_context = improved_rag.fetch_context
eval_mod.answer_question = improved_rag.answer_question


def main():
    print("Running retrieval evaluation (improved RAG: query rewrite + rerank)...")
    total_mrr = 0.0
    total_ndcg = 0.0
    total_cov = 0.0
    n = 0
    cat_mrr = defaultdict(list)
    for test, result, _ in eval_mod.evaluate_all_retrieval():
        n += 1
        total_mrr += result.mrr
        total_ndcg += result.ndcg
        total_cov += result.keyword_coverage
        cat_mrr[test.category].append(result.mrr)
    avg_mrr = total_mrr / n if n else 0
    avg_ndcg = total_ndcg / n if n else 0
    avg_cov = total_cov / n if n else 0
    print(f"  MRR: {avg_mrr:.4f}")
    print(f"  nDCG: {avg_ndcg:.4f}")
    print(f"  Keyword coverage: {avg_cov:.1f}%")
    print(f"  Tests: {n}")

    print("\nRunning answer evaluation (improved RAG)...")
    total_acc = 0.0
    total_comp = 0.0
    total_rel = 0.0
    n = 0
    cat_acc = defaultdict(list)
    for test, result, _ in eval_mod.evaluate_all_answers():
        n += 1
        total_acc += result.accuracy
        total_comp += result.completeness
        total_rel += result.relevance
        cat_acc[test.category].append(result.accuracy)
    avg_acc = total_acc / n if n else 0
    avg_comp = total_comp / n if n else 0
    avg_rel = total_rel / n if n else 0
    print(f"  Accuracy: {avg_acc:.2f}/5")
    print(f"  Completeness: {avg_comp:.2f}/5")
    print(f"  Relevance: {avg_rel:.2f}/5")
    print(f"  Tests: {n}")

    print("\nPer-category average accuracy (sample):")
    for cat in sorted(cat_acc.keys()):
        vals = cat_acc[cat]
        print(f"  {cat}: {sum(vals)/len(vals):.2f}/5 (n={len(vals)})")


if __name__ == "__main__":
    main()
