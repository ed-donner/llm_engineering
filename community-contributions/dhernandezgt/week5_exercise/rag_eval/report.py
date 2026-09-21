"""
Aggregates CaseResult rows into summary tables, stratified by
difficulty / question_type / source_doc, and flags the pattern
that best explains each failure (retrieval vs generation problem).
"""
from __future__ import annotations
from collections import defaultdict
from statistics import mean
from typing import List, Dict, Any

from .evaluator import CaseResult


def _avg(values):
    values = [v for v in values if v is not None]
    return round(mean(values), 3) if values else None


def summarize(results: List[CaseResult]) -> Dict[str, Any]:
    overall = {
        "n_cases": len(results),
        "retrieval_hit_rate": _avg([1 if r.retrieval_hit else 0 for r in results]),
        "retrieval_mrr": _avg([r.retrieval_mrr for r in results]),
        "context_precision": _avg([r.context_precision for r in results]),
        "keyword_coverage": _avg([r.keyword_coverage for r in results]),
        "assertion_coverage": _avg([r.assertion_coverage for r in results]),
        "answer_similarity": _avg([r.answer_similarity for r in results]),
    }

    def group_by(attr):
        buckets = defaultdict(list)
        for r in results:
            buckets[getattr(r, attr)].append(r)
        return {
            key: {
                "n": len(rows),
                "retrieval_hit_rate": _avg([1 if r.retrieval_hit else 0 for r in rows]),
                "context_precision": _avg([r.context_precision for r in rows]),
                "assertion_coverage": _avg([r.assertion_coverage for r in rows]),
                "answer_similarity": _avg([r.answer_similarity for r in rows]),
            }
            for key, rows in buckets.items()
        }

    return {
        "overall": overall,
        "by_difficulty": group_by("difficulty"),
        "by_question_type": group_by("question_type"),
        "by_source_doc": group_by("source_doc"),
    }


def diagnose(results: List[CaseResult],
             precision_threshold: float = 0.5,
             assertion_threshold: float = 0.7) -> Dict[str, List[str]]:
    """
    Buckets failing cases by likely root cause:
      - 'retrieval_failure': wrong/low-precision context retrieved -> fix retriever/chunking
      - 'generation_failure': context was fine but answer still missed assertions -> fix prompt/model
      - 'both_failed': neither retrieval nor generation worked
      - 'passing': met both thresholds
    """
    buckets = {"retrieval_failure": [], "generation_failure": [], "both_failed": [], "passing": []}
    for r in results:
        retrieval_ok = r.retrieval_hit and (r.context_precision or 0) >= precision_threshold
        generation_ok = (r.assertion_coverage is None) or (r.assertion_coverage >= assertion_threshold)
        if retrieval_ok and generation_ok:
            buckets["passing"].append(r.id)
        elif retrieval_ok and not generation_ok:
            buckets["generation_failure"].append(r.id)
        elif not retrieval_ok and generation_ok:
            buckets["retrieval_failure"].append(r.id)
        else:
            buckets["both_failed"].append(r.id)
    return buckets


def print_report(results: List[CaseResult]) -> None:
    summary = summarize(results)
    diag = diagnose(results)

    print("=" * 60)
    print("OVERALL")
    print("=" * 60)
    for k, v in summary["overall"].items():
        print(f"  {k}: {v}")

    for section in ["by_difficulty", "by_question_type", "by_source_doc"]:
        print("\n" + "=" * 60)
        print(section.upper())
        print("=" * 60)
        for key, stats in summary[section].items():
            print(f"  [{key}] n={stats['n']} "
                  f"hit_rate={stats['retrieval_hit_rate']} "
                  f"precision={stats['context_precision']} "
                  f"assertion_cov={stats['assertion_coverage']} "
                  f"answer_sim={stats['answer_similarity']}")

    print("\n" + "=" * 60)
    print("ROOT-CAUSE DIAGNOSIS")
    print("=" * 60)
    for cause, ids in diag.items():
        print(f"  {cause}: {len(ids)} case(s)")
