"""
Metrics for two independent stages of a RAG pipeline:

  1. Retrieval metrics  -> did we fetch the right context?
  2. Generation metrics -> given the context, did the answer satisfy
                            the required facts (assertions) and match
                            the gold answer?

Kept dependency-light (stdlib + sklearn TF-IDF) so it runs anywhere.
Swap `text_similarity()` for an embedding-based version if you have
one available (see `embedding_similarity_hook` in evaluator.py).
"""
from __future__ import annotations
import re
from difflib import SequenceMatcher
from typing import List, Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .mapping import source_matches


# ---------- Retrieval metrics ----------

def retrieval_hit(retrieved_sources: Sequence[str], gold_source_doc: str) -> bool:
    """Did ANY retrieved chunk come from the correct source document?"""
    return any(source_matches(s, gold_source_doc) for s in retrieved_sources)


def retrieval_mrr(retrieved_sources: Sequence[str], gold_source_doc: str) -> float:
    """Reciprocal rank of the first correctly-sourced chunk (0 if none)."""
    for i, s in enumerate(retrieved_sources, start=1):
        if source_matches(s, gold_source_doc):
            return 1.0 / i
    return 0.0


def context_precision(retrieved_sources: Sequence[str], gold_source_doc: str) -> float:
    """Fraction of retrieved chunks that come from the correct source doc."""
    if not retrieved_sources:
        return 0.0
    correct = sum(1 for s in retrieved_sources if source_matches(s, gold_source_doc))
    return correct / len(retrieved_sources)


def keyword_coverage(context_text: str, keywords: Sequence[str]) -> float:
    """Fraction of source_keywords found (case-insensitive substring) in retrieved context."""
    if not keywords:
        return None  # undefined, not zero, if no keywords were provided
    text_lower = context_text.lower()
    found = sum(1 for kw in keywords if kw.lower() in text_lower)
    return found / len(keywords)


# ---------- Generation metrics ----------

_STOPWORDS = {"a", "an", "the", "is", "are", "was", "were", "be", "been", "of", "to", "in",
              "on", "and", "or", "that", "this", "it", "as", "for", "with", "at", "answer"}


def _stem_candidates(word: str) -> set:
    """Returns multiple plausible stems for a word (not just one), since a single
    greedy suffix-strip mishandles cases like 'phases'->'phas' vs 'phase'->'phase'.
    Trying several candidates and matching on ANY is more robust than picking one."""
    cands = {word}
    if word.endswith("ing") and len(word) > 5:
        cands.add(word[:-3])
    if word.endswith("ed") and len(word) > 4:
        cands.add(word[:-2])
    if word.endswith("es") and len(word) > 4:
        cands.add(word[:-2])
        cands.add(word[:-1])  # e.g. 'phases' -> 'phase' (strip only the 's')
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        cands.add(word[:-1])
    return cands


def _content_word_stems(text: str) -> set:
    """Union of all stem candidates for all content words in text."""
    words = re.findall(r"[a-zA-Z']+", text.lower())
    stems = set()
    for w in words:
        if w not in _STOPWORDS and len(w) > 2:
            stems |= _stem_candidates(w)
    return stems


def _token_overlap(haystack: str, needle: str, threshold: float = 0.7) -> bool:
    """True if most of needle's content words (stem-aware) appear in haystack,
    regardless of order -- catches paraphrases like 'header is included' vs
    'includes the UDP header' that substring/sequence matching miss."""
    needle_words = re.findall(r"[a-zA-Z']+", needle.lower())
    needle_words = [w for w in needle_words if w not in _STOPWORDS and len(w) > 2]
    if not needle_words:
        return False
    haystack_stems = _content_word_stems(haystack)
    hits = sum(1 for w in needle_words if _stem_candidates(w) & haystack_stems)
    return (hits / len(needle_words)) >= threshold


def _fuzzy_contains(haystack: str, needle: str, threshold: float = 0.6) -> bool:
    """
    True if `needle` is substantively present in `haystack` (the generated
    answer). Tries, in order: exact substring, sentence-level fuzzy ratio
    (catches near-identical phrasing), then stem-aware token overlap
    (catches reordered/paraphrased wording).
    """
    needle = needle.strip().strip('"')
    if not needle:
        return True
    haystack_l, needle_l = haystack.lower(), needle.lower()
    if needle_l in haystack_l:
        return True
    sentences = re.split(r'(?<=[.!?])\s+', haystack)
    for sent in sentences:
        if SequenceMatcher(None, sent.lower(), needle_l).ratio() >= threshold:
            return True
    return _token_overlap(haystack, needle)


_QUOTED_RE = re.compile(r'"([^"]+)"')
_MENTIONS_RE = re.compile(r'\bmentions?\b\s*(.*)', re.IGNORECASE)
_LISTS_RE = re.compile(r'\blists?\b\s*(.*)', re.IGNORECASE)
_COUNT_RE = re.compile(r'\b(all|at least|exactly|at most)\s+(\d+)\b', re.IGNORECASE)

# Enumeration-marker patterns tried when an assertion requires counting items
# (e.g. "lists all 5 states"). Different documents enumerate differently, so
# several styles are tried and the best (max) count is used.
_ENUM_PATTERNS = [
    re.compile(r'\(\d{1,3}\)'),                                  # "Echo Reply (0), ... (16)"
    re.compile(r'(?:^|\s)\(?\d{1,2}[\.\)]\s'),                    # "1. ..." / "1) ..." numbered lists
    re.compile(r'\b(?:Class|Type|Phase|Step)\s+[A-Z0-9]+\b'),     # "Class A", "Phase 1", "Type 133"
    re.compile(r'\b[A-Z]{4,}\b\s*[—\-]'),                         # "INCOMPLETE —", "REACHABLE —"
]


def _is_count_assertion(text: str):
    """Returns (quantifier, n) if this assertion requires counting enumerated
    items in the answer (e.g. 'all 5 states', 'at least 5 message types'), else None."""
    m = _COUNT_RE.search(text)
    if not m:
        return None
    return m.group(1).lower(), int(m.group(2))


def _count_enumerated_items(text: str) -> int:
    """Best-effort count of distinct enumerated items in text, trying several
    common enumeration styles and taking the max (styles rarely mix within
    one answer, so summing would double count)."""
    return max((len(p.findall(text)) for p in _ENUM_PATTERNS), default=0)


def check_assertion(answer: str, assertion_text: str) -> bool:
    """
    Evaluates ONE natural-language assertion clause against the generated
    answer. Understands the common rule patterns found in this dataset:

      - answer contains "X"                   -> literal substring, case-insensitive
      - answer contains/mentions "X" or Y      -> EITHER the quoted literal OR the unquoted
                                                   alternative may satisfy it
      - answer mentions X/Y | X or Y           -> fuzzy presence of EITHER alt
      - answer lists A, B, C, D                -> ALL comma-separated items must be present
      - answer {mentions/lists} all/at least N X  -> heuristic count of enumerated items in
                                                       the answer compared against N (approximate --
                                                       see module docstring caveat)
      - anything else                          -> fuzzy match of the whole clause (fallback)

    Note: assertions are typically split on ';' upstream (loader.py), so
    each string passed here is usually a single self-contained check.
    """
    text = assertion_text.strip()
    if not text:
        return True

    # Count-based assertions ("all 3 classes", "at least 5 message types") can't be
    # resolved by literal/fuzzy text matching -- they require counting enumerated
    # items in the answer. Heuristic, deliberately lenient (>=N in all cases) since
    # under-flagging a correct answer is worse than over-crediting a borderline one.
    count_spec = _is_count_assertion(text)
    if count_spec:
        _, n = count_spec
        return _count_enumerated_items(answer) >= n

    # Parenthetical comma-list, e.g. "gives bit patterns (0, 10, 110)" -> ALL items required.
    # Checked before quoted/lists handling since it's a distinct, unambiguous format.
    paren_m = re.search(r'\(([^)]+,[^)]+)\)\s*$', text)
    if paren_m:
        items = [i.strip() for i in paren_m.group(1).split(',') if i.strip()]
        if items:
            return all(_fuzzy_contains(answer, item) for item in items)

    lists_m = _LISTS_RE.search(text)
    if lists_m and lists_m.group(1).strip():
        items = [i.strip() for i in re.split(r',|\band\b', lists_m.group(1)) if i.strip()]
        return all(_fuzzy_contains(answer, item) for item in items)

    quoted = _QUOTED_RE.findall(text)
    if quoted:
        # "X" or "Y" / X or "Y" / "X" or Y -> satisfied if ANY alternative is present.
        # Quoted spans are always literal candidates (checked via substring/fuzzy).
        # Additionally, any "or"-separated chunk that has NO quotes at all is also
        # a candidate in its own right (covers 'hysteresis or "accept existing DR"').
        candidates = list(quoted)
        phrase = re.sub(r'^\s*(?:answer\s+)?(?:contains?|mentions?)\s*', '', text, flags=re.IGNORECASE)
        for chunk in re.split(r'\s+\bor\b\s+', phrase):
            chunk = chunk.strip()
            if chunk and '"' not in chunk:
                candidates.append(chunk)
        return any(_fuzzy_contains(answer, c) for c in candidates)

    mentions_m = _MENTIONS_RE.search(text)
    if mentions_m and mentions_m.group(1).strip():
        phrase = mentions_m.group(1)
        alts = [a.strip() for a in re.split(r'\s*/\s*|\s+\bor\b\s+', phrase) if a.strip()]
        return any(_fuzzy_contains(answer, alt) for alt in alts)

    # Fallback: fuzzy match the whole clause
    return _fuzzy_contains(answer, text)


def is_heuristic_assertion(text: str) -> bool:
    """True if this assertion is scored via the approximate enumeration-counting
    heuristic rather than direct text matching -- flag these in reports so a
    human can spot-check them rather than trusting the automated score blindly."""
    return _is_count_assertion(text) is not None


def assertion_coverage(answer: str, assertions: Sequence[str]) -> float:
    """Fraction of required assertions satisfied by the generated answer."""
    if not assertions:
        return None
    hits = sum(1 for a in assertions if check_assertion(answer, a))
    return hits / len(assertions)


def failed_assertions(answer: str, assertions: Sequence[str]) -> List[str]:
    """List of assertions NOT satisfied by the answer -- useful for debugging."""
    return [a for a in assertions if not check_assertion(answer, a)]


def text_similarity(a: str, b: str) -> float:
    """TF-IDF cosine similarity between two texts (e.g. answer vs gold_answer)."""
    if not a or not b:
        return 0.0
    vect = TfidfVectorizer().fit([a, b])
    vecs = vect.transform([a, b])
    return float(cosine_similarity(vecs[0], vecs[1])[0][0])
