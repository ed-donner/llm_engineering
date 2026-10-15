# Tests implemented, and how to read their output

Three kinds of testing were done while building this framework. None of
them require a live LLM — they validate the framework itself, separate
from validating your actual RAG answers (that's what `run_real_eval.py`
is for).

## 1. Calibration test: does the assertion parser agree with its own gold data?

**What it does:** feeds each row's `gold_answer` back through its own
`assertions` list via `metrics.check_assertion()`. Since assertions were
written to describe the gold answer, a well-functioning parser should
score close to 100% — any failure here is either a parser bug or a
genuinely ambiguous assertion worth knowing about before you trust the
framework's judgment on real (non-gold) answers.

```python
from rag_eval.loader import load_eval_csv
from rag_eval.metrics import check_assertion, is_heuristic_assertion

cases = load_eval_csv("data/RFC_evaluation/rag_evaluation_dataset.csv")
total = passed = 0
for c in cases:
    for a in c.assertions:
        total += 1
        passed += check_assertion(c.gold_answer, a)
print(f"{passed}/{total} = {passed/total:.3f}")
```

**Result on this dataset:** `83/90 = 0.922`

**How to interpret it:**
- **~90%+ is a healthy result.** It means the rule-based parser (quoted
  literals, `X or Y` alternatives, `lists A, B, C`, count-based
  `all N X`) correctly recognizes the patterns actually used in your
  `assertions` column.
- **The remaining ~8% is a real, permanent ceiling for lexical matching**,
  not a bug to chase down further. Example failures:
  - Assertion expects literal `"10"`; gold answer expresses the same fact
    as `"1-0"` (bit-pattern notation).
  - Assertion says `"merging happens before opcode check"`; gold answer
    says `"examining the opcode"` — same meaning, no shared wording.

  These need semantic understanding, not string matching. If your real
  answers paraphrase concepts the way people naturally do, expect
  `assertion_coverage` to underestimate correctness by roughly this same
  margin. Treat `assertion_coverage` below ~0.85–0.90 on an otherwise
  good-looking answer as "check `failed_assertions` before assuming the
  answer is wrong" rather than an automatic fail.
- **Run this check on your own data before trusting scores from it.**
  If you ever revise the CSV's assertions, re-run this calibration —
  a big drop signals either a new assertion phrasing style the parser
  doesn't understand yet, or a genuine authoring inconsistency in the CSV.

## 2. Negative control: does the parser correctly reject wrong answers?

**What it does:** feeds a deliberately wrong answer (about an unrelated
topic) against a case's real assertions, and confirms none pass.

```python
wrong = "TCP is a connectionless protocol used for streaming video."
results = [check_assertion(wrong, a) for a in cases[3].assertions]
print(sum(results), "/", len(results), "false positives")
```

**Result:** `0/4` — the parser did not falsely credit an unrelated,
factually wrong answer. This matters because a parser that's too lenient
(e.g. matching on any word overlap) would make every score look better
than it is. Re-run this whenever you tune matching thresholds
(`_fuzzy_contains`'s `threshold=0.6`, `_token_overlap`'s `threshold=0.7`
in `metrics.py`) — loosening them improves recall on paraphrases but
risks reintroducing false positives like this.

## 3. Retry / incremental-save behavior test

**What it does:** runs a synthetic 3-question CSV through a deliberately
flaky pipeline function that (a) fails transiently twice then recovers,
and (b) fails permanently once, to confirm `evaluator.run_evaluation()`
handles both correctly without manual intervention.

```python
calls = {"n": 0}
def flaky_pipeline(question):
    calls["n"] += 1
    if calls["n"] in (2, 3):
        raise RuntimeError("503 UNAVAILABLE")   # transient
    if calls["n"] == 5:
        raise ValueError("bad prompt format")    # permanent
    return RagResult(retrieved_chunks=[...], generated_answer="some answer")

results = run_evaluation("mini.csv", flaky_pipeline, out_path="mini_results.csv",
                          max_retries=3, base_delay=0.1)
```

**Observed output:**
```
[1/3] id=1: question 1... ok (assertion_cov=n/a)
    [transient error, retry 1/3 in 0s] 503 UNAVAILABLE
    [transient error, retry 2/3 in 0s] 503 UNAVAILABLE
[2/3] id=2: question 2... ok (assertion_cov=n/a)
[3/3] id=3: question 3... FAILED (bad prompt format)

1/3 case(s) failed after 3 retries each:
  id=3: bad prompt format
(Completed results were saved incrementally; re-run just these ids once the issue clears.)

final in-memory results count: 2
```
And `mini_results.csv` on disk already contained the 2 completed rows —
written the moment each one finished, not only at the end.

**How to interpret this in a real run against your Gemini/Ollama pipeline:**
- A `[transient error, retry N/M in Xs] ...` line is expected and fine —
  it means a 503/429/timeout happened and is being retried automatically.
  You don't need to intervene.
- A line ending in `FAILED (...)` means retries were exhausted (transient)
  or the error wasn't considered transient at all (e.g. a `ValueError`
  from your own code) — that question was skipped, not silently dropped.
  Its `id` is listed in the end-of-run summary so you can re-run just that
  subset later.
- `eval_results.csv` is trustworthy to open **even mid-run or after a
  crash** — every row in it is a question that fully completed.

## 4. Reading `eval_results.csv` and the console report

**Per-row columns (`eval_results.csv`):**

| Column | Meaning | Range |
|---|---|---|
| `retrieval_hit` | Did *any* retrieved chunk come from the correct RFC? | `True`/`False` |
| `retrieval_mrr` | Reciprocal rank of the first correctly-sourced chunk (1.0 = it was ranked #1) | 0.0–1.0 |
| `context_precision` | Fraction of retrieved chunks from the correct RFC | 0.0–1.0 |
| `keyword_coverage` | Fraction of `source_keywords` found in the retrieved text (not the answer) | 0.0–1.0 or blank if no keywords listed |
| `assertion_coverage` | Fraction of `assertions` satisfied by the generated answer | 0.0–1.0 or blank if no assertions |
| `answer_similarity` | TF-IDF cosine similarity, generated answer vs `gold_answer` — a coarse sanity check, not a correctness measure | 0.0–1.0 |
| `failed_assertions` | Which specific assertions were NOT satisfied — read this before assuming a low score means a bad answer | text |
| `heuristic_assertions` | Which assertions in this row were count-based (approximate scoring) — spot-check these manually | text |

**Console report sections** (`report.print_report()`):
- **OVERALL** — sanity-check first. If `retrieval_hit_rate` is high but
  `assertion_coverage` is low across the board, your retriever is fine
  and the problem is in generation (prompt, model choice, context
  ordering). The reverse pattern points at retrieval/chunking instead.
- **BY_DIFFICULTY** — if `hard` questions don't score meaningfully lower
  than `easy` ones, the difficulty labels themselves may be miscalibrated
  — worth a manual relabel before trusting difficulty-based conclusions.
- **BY_QUESTION_TYPE** — a `comparative`/`procedural` type scoring worse
  than `factual` usually means your chunk size is too small to span
  multi-part answers, not a generation problem.
- **BY_SOURCE_DOC** — one RFC consistently underperforming suggests that
  specific file chunks badly (long ASCII diagrams, tables) rather than a
  general pipeline issue.
- **ROOT-CAUSE DIAGNOSIS** — buckets every case into `passing`,
  `retrieval_failure`, `generation_failure`, or `both_failed` using
  configurable thresholds (`precision_threshold=0.5`,
  `assertion_threshold=0.7` in `report.diagnose()`). Use this as your
  starting triage list, not a final verdict — combine it with reading the
  `failed_assertions` for individual `generation_failure` cases, since
  some of those will be lexical-matching misses (see the calibration
  section above) rather than real answer failures.
