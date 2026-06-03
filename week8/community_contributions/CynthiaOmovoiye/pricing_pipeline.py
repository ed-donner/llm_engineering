# pricing_pipeline.py – Week 8 price-attack pipeline
# Data build, retrieval, and evaluation helpers for The Price is Right.

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np
import pandas as pd

# Optional deps: fail loudly only when the feature is used
def _require(module: str):
    try:
        return __import__(module)
    except ImportError as e:
        raise ImportError(f"Install {module} for this feature. {e}") from e


# --- Constants (match course) ---
CATEGORY_NAMES = [
    "Automotive",
    "Electronics",
    "Office_Products",
    "Tools_and_Home_Improvement",
    "Cell_Phones_and_Accessories",
    "Toys_and_Games",
    "Appliances",
    "Musical_Instruments",
]

# Configurable price bands (as in spec)
DEFAULT_PRICE_BINS = [0, 25, 50, 100, 200, 350, 500, 1000]
MIN_PRICE = 0.50
MAX_PRICE = 999.49
MIN_CHARS = 600
MAX_TEXT_EACH = 3000
MAX_TEXT_TOTAL = 4000
REMOVALS = [
    "Part Number",
    "Best Sellers Rank",
    "Batteries Included?",
    "Batteries Required?",
    "Item model number",
]
RANDOM_STATE = 42
EVAL_SIZE = 200


def _norm(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (s or "").lower().strip())


def get_weight(details: dict) -> float:
    w = details.get("Item Weight") or details.get("item weight")
    if not w:
        return 0.0
    parts = str(w).split()
    if len(parts) < 2:
        return 0.0
    try:
        amt = float(parts[0])
    except ValueError:
        return 0.0
    u = parts[1].lower()
    if u == "pounds":
        return amt
    if u == "ounces":
        return amt / 16
    if u == "grams":
        return amt / 453.592
    if u == "kilograms":
        return amt * 2.20462
    return 0.0


def get_brand(details: dict) -> str:
    if not details:
        return ""
    b = details.get("Brand") or details.get("brand") or details.get("Manufacturer") or details.get("manufacturer")
    return (b or "").strip()[:200]


def simplify(t: Any) -> str:
    """Convert to single-line text; flatten lists/dicts to readable form (no Python repr)."""
    if t is None:
        return ""
    if isinstance(t, list):
        parts = [simplify(x) for x in t if x is not None]
        s = " ".join(p for p in parts if p)
    elif isinstance(t, dict):
        parts = [f"{k}: {simplify(v)}" for k, v in t.items() if v is not None]
        s = " ".join(parts)
    else:
        s = str(t)
    s = s.replace("\n", " ").replace("\r", "").replace("\t", "").replace("  ", " ").strip()
    return s[:MAX_TEXT_EACH]


def scrub(title: str, description: Any, features: Any, details: dict) -> str:
    details = dict(details or {})
    for r in REMOVALS:
        details.pop(r, None)
    out = (title or "") + "\n"
    if description:
        out += simplify(description) + "\n"
    if features:
        out += simplify(features) + "\n"
    if details:
        out += json.dumps(details) + "\n"
    out = re.sub(
        r"\b(?=[A-Z0-9]{7,}\b)(?=.*[A-Z])(?=.*\d)[A-Z0-9]+\b",
        "",
        out,
    ).strip()[:MAX_TEXT_TOTAL]
    return out


def parse_raw_row(row: dict, category: str, item_cls: type) -> Optional[Any]:
    """Parse one row from Amazon-Reviews-2023 raw_meta_* into Item (or item_cls)."""
    try:
        price = float(row["price"])
    except (ValueError, TypeError):
        return None
    if not (MIN_PRICE <= price <= MAX_PRICE):
        return None
    title = row.get("title") or ""
    description = row.get("description")
    features = row.get("features")
    raw_details = row.get("details")
    if isinstance(raw_details, str):
        try:
            details = json.loads(raw_details)
        except Exception:
            details = {}
    else:
        details = raw_details or {}
    weight = get_weight(details)
    brand = get_brand(details)
    full = scrub(title, description, features, details)
    if brand:
        full = f"Brand: {brand}\n{full}"
    if len(full) < MIN_CHARS:
        return None
    # Item has: title, category, price, full, weight, summary (optional)
    return item_cls(
        title=title,
        category=category,
        price=price,
        full=full,
        weight=weight if weight else None,
        summary=full[:2000],
    )


def dedup_key(item: Any) -> str:
    title = getattr(item, "title", "") or ""
    full = getattr(item, "full", None) or getattr(item, "summary", None) or ""
    return _norm(title) + " | " + _norm(full)


def price_band(price: float, bins: list[float]) -> tuple[float, float]:
    for i in range(len(bins) - 1):
        if bins[i] <= price < bins[i + 1]:
            return (bins[i], bins[i + 1])
    return (bins[-2], bins[-1])


def build_support_from_raw(
    load_dataset_fn: Callable,
    item_cls: type,
    frozen_eval_keys: set[str],
    price_bins: Optional[list[float]] = None,
    target_per_bucket: int = 400,
    cache_path: Optional[Path] = None,
) -> list[Any]:
    """
    Load 8 categories from Amazon-Reviews-2023, parse, dedupe, exclude eval overlap,
    stratified sample by (category, price_band). Returns list of item_cls instances.
    """
    if price_bins is None:
        price_bins = DEFAULT_PRICE_BINS

    if cache_path and cache_path.exists():
        with open(cache_path) as f:
            data = json.load(f)
        return [item_cls.model_validate(d) for d in data]

    raw_items = []
    for cat in CATEGORY_NAMES:
        try:
            ds = load_dataset_fn("McAuley-Lab/Amazon-Reviews-2023", f"raw_meta_{cat}", "full")
        except Exception as e:
            raise RuntimeError(f"Failed to load raw_meta_{cat}: {e}") from e
        for row in ds:
            it = parse_raw_row(row, cat, item_cls)
            if it is not None:
                raw_items.append(it)

    seen = set()
    deduped = []
    for it in raw_items:
        k = dedup_key(it)
        if k in frozen_eval_keys or k in seen:
            continue
        seen.add(k)
        deduped.append(it)

    rng = np.random.default_rng(RANDOM_STATE)
    buckets = {}
    for it in deduped:
        band = price_band(it.price, price_bins)
        key = (it.category, band)
        buckets.setdefault(key, []).append(it)

    support_items = []
    for key, lst in buckets.items():
        if len(lst) <= target_per_bucket:
            support_items.extend(lst)
        else:
            idx = rng.choice(len(lst), size=target_per_bucket, replace=False)
            support_items.extend([lst[i] for i in idx])

    rng.shuffle(support_items)

    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump([it.model_dump() for it in support_items], f, indent=0)

    return support_items


def product_text(item: Any, include_weight: bool = True) -> str:
    """Normalized product text: title, category, brand, weight, description."""
    parts = [f"Title: {getattr(item, 'title', '') or ''}", f"Category: {getattr(item, 'category', '') or ''}"]
    brand = getattr(item, "brand", None) or ""
    if brand:
        parts.append(f"Brand: {brand}")
    if include_weight:
        w = getattr(item, "weight", None)
        if w is not None and w > 0:
            parts.append(f"Weight: {w}")
    full = getattr(item, "full", None) or getattr(item, "summary", None) or ""
    if full:
        parts.append(f"Description: {full[:3000]}")
    return "\n".join(parts).strip()


def build_tfidf_index(texts: list[str], max_features: int = 8000, ngram_range: tuple[int, int] = (1, 2)):
    sklearn = _require("sklearn")
    vec = sklearn.feature_extraction.text.TfidfVectorizer(
        max_features=max_features,
        stop_words="english",
        ngram_range=ngram_range,
    )
    mat = vec.fit_transform(texts)
    return vec, mat


def build_dense_index(
    texts: list[str],
    model_name: str = "BAAI/bge-small-en-v1.5",
    cache_path: Optional[Path] = None,
    device: Optional[str] = None,
):
    """Build dense embeddings with sentence-transformers. Returns (model, embeddings matrix)."""
    if cache_path and cache_path.exists():
        emb = np.load(cache_path)
        return None, emb
    st = _require("sentence_transformers")
    model = st.SentenceTransformer(model_name, device=device)
    emb = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(cache_path, emb)
    return model, emb


def retrieve_tfidf(
    query_text: str,
    pool_texts: list[str],
    pool_items: list[Any],
    vectorizer: Any,
    pool_mat: Any,
    k: int = 5,
    exclude_key: Optional[str] = None,
    dedup_key_fn: Callable[[Any], str] = dedup_key,
):
    sklearn = _require("sklearn")
    qvec = vectorizer.transform([query_text])
    sim = sklearn.metrics.pairwise.cosine_similarity(qvec, pool_mat).ravel()
    order = np.argsort(-sim)
    out = []
    for i in order:
        if len(out) >= k:
            break
        cand = pool_items[i]
        if exclude_key and dedup_key_fn(cand) == exclude_key:
            continue
        out.append((cand, float(sim[i])))
    return out


def load_embedding_model(model_name: str = "BAAI/bge-small-en-v1.5", device: Optional[str] = None):
    """Load sentence-transformers model (e.g. when embeddings were loaded from cache)."""
    st = _require("sentence_transformers")
    return st.SentenceTransformer(model_name, device=device)


def retrieve_dense(
    query_text: str,
    pool_emb: np.ndarray,
    pool_items: list[Any],
    model: Any,
    k: int = 5,
    exclude_key: Optional[str] = None,
    dedup_key_fn: Callable[[Any], str] = dedup_key,
):
    if model is None:
        raise ValueError("Dense retrieval requires a loaded model when cache was used for embeddings only")
    qemb = model.encode([query_text], convert_to_numpy=True)
    norms = np.linalg.norm(pool_emb, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-9, norms)
    qn = np.linalg.norm(qemb) or 1e-9
    sim = (np.dot(qemb, pool_emb.T).ravel() / (qn * norms.ravel())).clip(-1, 1)
    order = np.argsort(-sim)
    out = []
    for i in order:
        if len(out) >= k:
            break
        cand = pool_items[i]
        if exclude_key and dedup_key_fn(cand) == exclude_key:
            continue
        out.append((cand, float(sim[i])))
    return out


def mmr_select(
    scored: list[tuple[Any, float]],
    pool_texts: list[str],
    pool_items: list[Any],
    lambda_: float = 0.7,
    k: int = 5,
) -> list[Any]:
    """Maximal marginal relevance: balance relevance and diversity. scored = [(item, score), ...]."""
    if not scored or k <= 0:
        return []
    idx_map = {id(pool_items[i]): i for i in range(len(pool_items))}
    text_by_id = {id(pool_items[i]): pool_texts[i] for i in range(len(pool_items))}
    selected = []
    selected_ids = set()
    remaining = list(scored)
    while len(selected) < k and remaining:
        best_score = -1e9
        best_idx = -1
        for idx, (item, rel) in enumerate(remaining):
            if id(item) in selected_ids:
                continue
            # MMR: lambda * rel - (1-lambda) * max_sim to selected
            if not selected:
                mmr = rel
            else:
                sim_to_selected = []
                for s in selected:
                    ti = text_by_id.get(id(s), "")
                    tj = text_by_id.get(id(item), "")
                    if ti and tj:
                        # simple Jaccard for diversity
                        a, b = set(ti.lower().split()), set(tj.lower().split())
                        inter = len(a & b)
                        union = len(a | b) or 1
                        sim_to_selected.append(inter / union)
                    else:
                        sim_to_selected.append(0.0)
                max_sim = max(sim_to_selected) if sim_to_selected else 0.0
                mmr = lambda_ * rel - (1 - lambda_) * max_sim
            if mmr > best_score:
                best_score = mmr
                best_idx = idx
        if best_idx < 0:
            break
        chosen = remaining.pop(best_idx)
        selected.append(chosen[0])
        selected_ids.add(id(chosen[0]))
    return selected


def neighbor_price_stats(items: list[Any]) -> dict[str, float]:
    prices = [getattr(it, "price", 0) for it in items if getattr(it, "price", None) is not None]
    if not prices:
        return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "std": 0.0, "q25": 0.0, "q75": 0.0}
    arr = np.array(prices)
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "std": float(np.std(arr)) if len(arr) > 1 else 0.0,
        "q25": float(np.percentile(arr, 25)),
        "q75": float(np.percentile(arr, 75)),
    }


def indices_same_category_and_band(
    pool_items: list[Any],
    category: str,
    price: float,
    price_bins: list[float],
    adjacent: bool = True,
) -> list[int]:
    """Indices into pool_items with same category and same (or adjacent if adjacent=True) price band."""
    band = price_band(price, price_bins)
    band_idx = next((i for i in range(len(price_bins) - 1) if (price_bins[i], price_bins[i + 1]) == band), 0)
    if adjacent:
        bands_ok = [
            (price_bins[j], price_bins[j + 1])
            for j in range(max(0, band_idx - 1), min(len(price_bins) - 1, band_idx + 2))
        ]
    else:
        bands_ok = [band]
    out = []
    for i, it in enumerate(pool_items):
        if getattr(it, "category", "") != category:
            continue
        if price_band(getattr(it, "price", 0), price_bins) in bands_ok:
            out.append(i)
    return out


def detect_device() -> str:
    """Return 'cuda', 'mps', or 'cpu'. Prefer CUDA, then MPS (Apple), then CPU."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


def has_mlx() -> bool:
    try:
        import mlx.core
        return True
    except ImportError:
        return False


def has_bitsandbytes() -> bool:
    try:
        import bitsandbytes
        return True
    except ImportError:
        return False


def metrics(truths: list[float], guesses: list[float]) -> dict[str, float]:
    t = np.asarray(truths, dtype=float)
    g = np.asarray(guesses, dtype=float)
    aae = float(np.mean(np.abs(g - t)))
    mse = float(np.mean((g - t) ** 2))
    ss_res = np.sum((t - g) ** 2)
    ss_tot = np.sum((t - np.mean(t)) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0
    return {"AAE": aae, "MSE": mse, "R2": r2}
