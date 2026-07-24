"""
Orchestrates evaluation: for each EvalCase, calls YOUR rag pipeline
(a function you provide), then scores retrieval + generation.

Your pipeline function must have this signature:

    def rag_pipeline(question: str) -> RagResult:
        ...

where RagResult carries the retrieved chunks (with their source paths)
and the final generated answer. This module doesn't care HOW you
retrieve/generate (vector DB, BM25, whatever) -- it only needs that
output shape.

Includes retry-on-transient-error (e.g. 503 UNAVAILABLE, 429 rate limit)
and incremental result saving, since a 30-question run against a live LLM
API can fail partway through -- you shouldn't lose everything before it
when that happens.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List, Optional
import csv
import sys
import time

from .loader import EvalCase, load_eval_csv
from . import metrics as M


@dataclass
class RetrievedChunk:
    source: str        # e.g. "txt/ipv4/RFC791_IPv4.txt" or just "RFC791"
    text: str
    score: Optional[float] = None


@dataclass
class RagResult:
    retrieved_chunks: List[RetrievedChunk]
    generated_answer: str


@dataclass
class CaseResult:
    id: str
    difficulty: str
    question_type: str
    source_doc: str
    retrieval_hit: bool
    retrieval_mrr: float
    context_precision: float
    keyword_coverage: Optional[float]
    assertion_coverage: Optional[float]
    answer_similarity: float
    failed_assertions: List[str]
    heuristic_assertions: List[str]  # count-based assertions scored approximately -- spot check these
    generated_answer: str


# ---------- retry handling ----------

# Substrings that identify a TRANSIENT failure worth retrying (server overload,
# rate limiting, network blips) as opposed to a real bug in your code, which
# should surface immediately rather than being silently retried 5 times.
_TRANSIENT_MARKERS = (
    "503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "RATE_LIMIT",
    "timeout", "Timeout", "Connection", "temporarily",
)


def _is_transient(exc: Exception) -> bool:
    msg = str(exc)
    return any(marker in msg for marker in _TRANSIENT_MARKERS) or isinstance(
        exc, (ConnectionError, TimeoutError)
    )


def _call_with_retry(fn, *args, max_retries: int = 5, base_delay: float = 5.0, **kwargs):
    """Calls fn(*args, **kwargs), retrying with exponential backoff on
    transient-looking errors. Re-raises immediately on anything else, or
    once retries are exhausted."""
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if not _is_transient(e) or attempt == max_retries:
                raise
            delay = base_delay * (2 ** (attempt - 1))
            print(f"    [transient error, retry {attempt}/{max_retries} in {delay:.0f}s] {e}",
                  file=sys.stderr)
            time.sleep(delay)
    raise last_exc  # pragma: no cover


# ---------- evaluation ----------

def evaluate_case(case: EvalCase, rag_pipeline: Callable[[str], RagResult],
                   max_retries: int = 5, base_delay: float = 5.0) -> CaseResult:
    result = _call_with_retry(rag_pipeline, case.question,
                               max_retries=max_retries, base_delay=base_delay)
    sources = [c.source for c in result.retrieved_chunks]
    context_text = "\n".join(c.text for c in result.retrieved_chunks)

    return CaseResult(
        id=case.id,
        difficulty=case.difficulty,
        question_type=case.question_type,
        source_doc=case.source_doc,
        retrieval_hit=M.retrieval_hit(sources, case.source_doc),
        retrieval_mrr=M.retrieval_mrr(sources, case.source_doc),
        context_precision=M.context_precision(sources, case.source_doc),
        keyword_coverage=M.keyword_coverage(context_text, case.source_keywords),
        assertion_coverage=M.assertion_coverage(result.generated_answer, case.assertions),
        answer_similarity=M.text_similarity(result.generated_answer, case.gold_answer),
        failed_assertions=M.failed_assertions(result.generated_answer, case.assertions),
        heuristic_assertions=[a for a in case.assertions if M.is_heuristic_assertion(a)],
        generated_answer=result.generated_answer,
    )


_FIELDNAMES = ["id", "difficulty", "question_type", "source_doc",
               "retrieval_hit", "retrieval_mrr", "context_precision",
               "keyword_coverage", "assertion_coverage", "answer_similarity",
               "failed_assertions", "heuristic_assertions", "generated_answer"]


def _result_to_row(r: CaseResult) -> dict:
    row = r.__dict__.copy()
    row["failed_assertions"] = " | ".join(r.failed_assertions)
    row["heuristic_assertions"] = " | ".join(r.heuristic_assertions)
    return row


def run_evaluation(csv_path: str, rag_pipeline: Callable[[str], RagResult],
                    out_path: Optional[str] = None, max_retries: int = 5,
                    base_delay: float = 5.0, verbose: bool = True) -> List[CaseResult]:
    """
    Runs every case in csv_path through rag_pipeline and scores it.

    out_path: if given, each result is written to this CSV THE MOMENT it
      completes (flushed to disk immediately) -- so if a later question
      crashes or hits an unrecoverable error, everything before it is
      already saved on disk, not just held in memory.
    max_retries / base_delay: retry behavior for transient errors (503,
      429, network blips) -- exponential backoff starting at base_delay
      seconds. Real (non-transient) errors are NOT retried.
    verbose: print one line of progress per question as it completes.

    A case that still fails after all retries is logged and SKIPPED --
    it does not abort the rest of the run. Failed ids are printed in a
    summary at the end so you know exactly what to re-run.
    """
    cases = load_eval_csv(csv_path)
    results: List[CaseResult] = []
    failed: List[tuple] = []

    f = writer = None
    if out_path:
        f = open(out_path, "w", newline="", encoding="utf-8")
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
        writer.writeheader()

    try:
        for i, case in enumerate(cases, start=1):
            if verbose:
                print(f"[{i}/{len(cases)}] id={case.id}: {case.question[:60]}...", end=" ", flush=True)
            try:
                result = evaluate_case(case, rag_pipeline, max_retries=max_retries, base_delay=base_delay)
            except Exception as e:
                failed.append((case.id, str(e)))
                if verbose:
                    print(f"FAILED ({e})")
                continue

            results.append(result)
            if verbose:
                cov = result.assertion_coverage
                cov_str = f"assertion_cov={cov:.2f}" if cov is not None else "assertion_cov=n/a"
                print(f"ok ({cov_str})")

            if writer:
                writer.writerow(_result_to_row(result))
                f.flush()
    finally:
        if f:
            f.close()

    if failed:
        print(f"\n{len(failed)}/{len(cases)} case(s) failed after {max_retries} retries each:", file=sys.stderr)
        for cid, msg in failed:
            print(f"  id={cid}: {msg}", file=sys.stderr)
        print("(Completed results were saved incrementally; re-run just these ids once the issue clears.)",
              file=sys.stderr)

    return results


def save_results_csv(results: List[CaseResult], out_path: str) -> None:
    """One-shot save of a full results list (e.g. after run_evaluation() returns).
    If you passed out_path= to run_evaluation() directly, this is redundant but
    harmless -- useful for re-saving after post-processing results in memory."""
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
        writer.writeheader()
        for r in results:
            writer.writerow(_result_to_row(r))
        