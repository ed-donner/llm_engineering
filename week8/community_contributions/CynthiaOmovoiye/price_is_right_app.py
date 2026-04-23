#!/usr/bin/env python3
"""
Week 8: The Price is Right — Self-contained local implementation.
Stage 5 hybrid reuses pricing_pipeline logic. Builds support from items_lite.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, List, Optional

# --- Path setup ---
REPO_ROOT = Path(__file__).resolve().parents[3]
WEEK8_ROOT = REPO_ROOT / "week8"
SUBMISSION_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(WEEK8_ROOT))
sys.path.insert(0, str(SUBMISSION_DIR))  # pricing_pipeline, same dir as this script

# Load env early
try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env", override=True)
    load_dotenv(SUBMISSION_DIR / ".env", override=True)
except ImportError:
    pass

# --- Config (explicit, fail loudly) ---
# All caches live in Week 8 submission dir
WEEK8_CACHE_DIR = SUBMISSION_DIR / "cache"
WEEK8_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# LiteLLM = open-source default (ollama). No paid API required.
CONFIG = {
    "CACHE_DIR": WEEK8_CACHE_DIR,
    "SUPPORT_JSON": WEEK8_CACHE_DIR / "support.json",
    "SUPPORT_EMB_NPY": WEEK8_CACHE_DIR / "support_emb_bge_small.npy",
    "CHROMA_DB_PATH": SUBMISSION_DIR / "products_vectorstore",
    "MEMORY_JSON": SUBMISSION_DIR / "memory.json",
    "BLEND_W": 0.35,  # Stage 5 regressor weight (lower = trust neighbor median more)
    "LITELLM_MODEL": os.getenv("LITELLM_MODEL", "ollama/llama3.2"),  # open-source default
    "FRONTIER_MODEL": os.getenv("FRONTIER_MODEL") or os.getenv("LITELLM_MODEL", "ollama/llama3.2"),
    "SCANNER_MODEL": os.getenv("SCANNER_MODEL") or os.getenv("LITELLM_MODEL", "ollama/llama3.2"),
    "DEAL_THRESHOLD": 50.0,
    "ENSEMBLE_SPECIALIST_W": 0.5,
    "ENSEMBLE_FRONTIER_W": 0.5,
}


# --- Pydantic models (from week8/agents/deals) ---
from pydantic import BaseModel, Field


class Deal(BaseModel):
    product_description: str = Field(description="Summary of the product")
    price: float = Field(description="Actual price")
    url: str = Field(description="URL of the deal")


class DealSelection(BaseModel):
    deals: List[Deal] = Field(description="Selected deals")


class Opportunity(BaseModel):
    deal: Deal
    estimate: float
    discount: float


# --- Agent base ---
class Agent:
    RED, GREEN, YELLOW, BLUE, CYAN, WHITE = "\033[31m", "\033[32m", "\033[33m", "\033[34m", "\033[36m", "\033[37m"
    BG_BLACK, RESET = "\033[40m", "\033[0m"
    name = ""
    color = "\033[37m"

    def log(self, msg: str):
        logging.info(self.BG_BLACK + self.color + f"[{self.name}] {msg}" + self.RESET)


# --- Stage 5 Specialist (from Week 7) ---
def _build_support_from_items_lite(support_path: Path, emb_path: Path) -> None:
    """Build support pool from items_lite. Requires HF_TOKEN."""
    try:
        from agents.items import Item
    except ImportError as e:
        raise ImportError("Need agents.items for items_lite") from e
    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError(
            "HF_TOKEN required. Get one at huggingface.co/settings/tokens and add to .env"
        )
    try:
        from huggingface_hub import login
        login(token=token, add_to_git_credential=False)
    except ImportError:
        pass
    train, _, _ = Item.from_hub("ed-donner/items_lite")
    import random
    rng = random.Random(42)
    sample = rng.sample(train, min(2000, len(train)))
    support_path.parent.mkdir(parents=True, exist_ok=True)
    with open(support_path, "w") as f:
        json.dump([it.model_dump() for it in sample], f, indent=0)
    from sentence_transformers import SentenceTransformer
    import numpy as np
    texts = [(it.full or it.summary or it.title or "")[:3000] for it in sample]
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    emb = model.encode(texts, show_progress_bar=True)
    emb_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(emb_path, emb)
    logging.info(f"Built support: {len(sample)} items at {support_path}")


def _ensure_support() -> tuple[list, Any, Any]:
    """Load support pool and embeddings. Builds from items_lite if cache missing."""
    support_path = CONFIG["SUPPORT_JSON"]
    emb_path = CONFIG["SUPPORT_EMB_NPY"]
    if not support_path.exists() or not emb_path.exists():
        _build_support_from_items_lite(support_path, emb_path)
    with open(support_path) as f:
        data = json.load(f)
    from types import SimpleNamespace
    support_items = [SimpleNamespace(**d) for d in data]
    import numpy as np
    emb = np.load(emb_path)
    # Load BGE model for inference (embeddings were built with BGE)
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return support_items, emb, model


def _build_stage5_predictor() -> Callable[[str], float]:
    """Build Stage 5 hybrid predictor (reuses pricing_pipeline logic). Returns price(description) -> float."""
    from types import SimpleNamespace
    import numpy as np
    from sklearn.preprocessing import LabelEncoder

    support_items, support_emb, dense_model = _ensure_support()
    support_texts = []
    for it in support_items:
        parts = [f"Title: {getattr(it, 'title', '') or ''}", f"Category: {getattr(it, 'category', '') or ''}"]
        full = getattr(it, "full", None) or getattr(it, "summary", None) or ""
        if full:
            parts.append(f"Description: {full[:3000]}")
        support_texts.append("\n".join(parts).strip())

    # Import pricing_pipeline helpers
    import pricing_pipeline as pp

    UNKNOWN_CAT = "__unknown__"
    cat_encoder = LabelEncoder()
    cat_encoder.fit(list(pp.CATEGORY_NAMES) + [UNKNOWN_CAT])
    NEIGHBOR_STAT_KEYS = ["mean", "median", "std", "min", "max", "q25", "q75"]
    K = 10  # more neighbors = more stable median
    blend_w = CONFIG["BLEND_W"]
    blend_w_unknown = 0.2  # when category unknown, trust regressor less

    # Train regressor (same logic as Week 7)
    def _featurize(item, neighbor_stats=None, emb_row=None):
        cat = (getattr(item, "category", "") or "").strip()
        if cat not in cat_encoder.classes_:
            cat = UNKNOWN_CAT
        cat_idx = cat_encoder.transform([cat])[0]
        text_len = len(pp.product_text(item))
        w = getattr(item, "weight", None) or 0.0
        base = [text_len, w, cat_idx]
        if neighbor_stats:
            base.extend([neighbor_stats.get(k, 0.0) for k in NEIGHBOR_STAT_KEYS])
        else:
            base.extend([0.0] * len(NEIGHBOR_STAT_KEYS))
        if emb_row is not None:
            base = list(emb_row) + base
        return base

    X_train, y_train = [], []
    for i, it in enumerate(support_items):
        qtext = pp.product_text(it)
        qemb = dense_model.encode([qtext], convert_to_numpy=True)[0]
        from sklearn.metrics.pairwise import cosine_similarity
        sim = cosine_similarity([qemb], support_emb).ravel()
        order = np.argsort(-sim)
        neighbors = [support_items[j] for j in order if j != i][:K]
        stats = pp.neighbor_price_stats(neighbors)
        row = _featurize(it, neighbor_stats=stats, emb_row=qemb)
        X_train.append(row)
        y_train.append(it.price)
    X_train = np.array(X_train, dtype=float)
    y_train = np.array(y_train)

    try:
        from xgboost import XGBRegressor
        reg = XGBRegressor(n_estimators=200, random_state=42)
    except ImportError:
        from sklearn.ensemble import RandomForestRegressor
        reg = RandomForestRegressor(n_estimators=100, random_state=42)
    reg.fit(X_train, y_train)

    def _retrieve_neighbors(description: str, k: int = K):
        item = SimpleNamespace(title="", category="", full=description, summary=description, weight=0)
        qtext = pp.product_text(item)
        qemb = dense_model.encode([qtext], convert_to_numpy=True)
        sim = (np.dot(qemb, support_emb.T) / (np.linalg.norm(qemb) * np.linalg.norm(support_emb, axis=1) + 1e-9)).ravel()
        order = np.argsort(-sim)[:k]
        return [support_items[i] for i in order]

    def _infer_category(neighbors: list) -> str:
        """Most common category among neighbors (support items have .category)."""
        from collections import Counter
        cats = [getattr(n, "category", "") or "" for n in neighbors]
        cats = [c for c in cats if c in cat_encoder.classes_]
        if not cats:
            return UNKNOWN_CAT
        return Counter(cats).most_common(1)[0][0]

    def price(description: str) -> float:
        item = SimpleNamespace(title="", category="", full=description, summary=description, weight=0)
        neighbors = _retrieve_neighbors(description, k=K)
        stats = pp.neighbor_price_stats(neighbors)
        median = stats["median"]
        n_min, n_max = stats["min"], stats["max"]
        # Infer category from neighbors so we use a real category instead of unknown
        item.category = _infer_category(neighbors)
        cat = item.category if item.category in cat_encoder.classes_ else UNKNOWN_CAT
        w = blend_w_unknown if cat == UNKNOWN_CAT else blend_w
        qtext = pp.product_text(item)
        cat_idx = cat_encoder.transform([cat])[0]
        meta = [len(qtext), 0.0, cat_idx] + [stats.get(k, 0.0) for k in NEIGHBOR_STAT_KEYS]
        qemb = dense_model.encode([qtext], convert_to_numpy=True)[0]
        row = np.concatenate([qemb, meta]).reshape(1, -1)
        if row.shape[1] != X_train.shape[1]:
            row = np.pad(row, ((0, 0), (0, max(0, X_train.shape[1] - row.shape[1]))), constant_values=0)[:, :X_train.shape[1]]
        reg_pred = float(reg.predict(row)[0])
        raw = w * reg_pred + (1 - w) * median
        # Clip to neighbor range (with margin) so hybrid stays grounded
        low = max(0.5, 0.5 * n_min) if n_min > 0 else 0.5
        high = 2.0 * n_max if n_max > 0 else 10000.0
        return float(np.clip(raw, low, high))

    return price


class LocalSpecialistAgent(Agent):
    name = "Specialist Agent (Stage 5)"
    color = Agent.RED
    _predictor = None

    def __init__(self):
        self.log("Initializing local Stage 5 specialist (no Modal)")
        if LocalSpecialistAgent._predictor is None:
            LocalSpecialistAgent._predictor = _build_stage5_predictor()
        self._predictor = LocalSpecialistAgent._predictor
        self.log("Specialist Agent ready")

    def price(self, description: str) -> float:
        self.log("Specialist Agent predicting")
        result = self._predictor(description)
        self.log(f"Specialist Agent: ${result:.2f}")
        return result


# --- Chroma build (for Frontier) ---
def build_chroma_from_support(chroma_path: Path, support_path: Path) -> None:
    """Build Chroma DB from support JSON. Uses all-MiniLM for compatibility with FrontierAgent."""
    import chromadb
    from sentence_transformers import SentenceTransformer
    with open(support_path) as f:
        items = json.load(f)
    encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    chroma_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_path))
    try:
        client.delete_collection("products")
    except Exception:
        pass
    coll = client.get_or_create_collection("products")
    batch_size = 500
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        docs = [(x.get("full") or x.get("summary") or x.get("title", ""))[:4000] for x in batch]
        metas = [{"category": x.get("category", ""), "price": float(x.get("price", 0))} for x in batch]
        ids = [f"doc_{i+j}" for j in range(len(batch))]
        embs = encoder.encode(docs).astype(float).tolist()
        coll.add(ids=ids, documents=docs, embeddings=embs, metadatas=metas)
    logging.info(f"Chroma built: {len(items)} docs at {chroma_path}")


# --- Frontier Agent ---
class LocalFrontierAgent(Agent):
    name = "Frontier Agent"
    color = Agent.BLUE

    def __init__(self, collection):
        self.log("Initializing Frontier Agent")
        self.collection = collection
        self.model = __import__("sentence_transformers", fromlist=["SentenceTransformer"]).SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        self._client = None
        self._ensure_llm()
        self.log("Frontier Agent ready")

    def _ensure_llm(self):
        # Prefer LiteLLM (open-source via Ollama). Optional: use OpenAI if key is set and is real OpenAI.
        try:
            __import__("litellm")
            self._client = "litellm"
            self._model = CONFIG["FRONTIER_MODEL"]
            self.log(f"Frontier using LiteLLM model: {self._model}")
            return
        except ImportError:
            pass
        key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if key and key.startswith("sk-") and not key.startswith("sk-or-"):
            try:
                self._client = __import__("openai", fromlist=["OpenAI"]).OpenAI()
                self._model = "gpt-4o-mini"
                self.log("Frontier using OpenAI (no litellm)")
                return
            except Exception:
                pass
        self._client = None
        self._model = None
        self.log("Frontier: no LLM; will use neighbor median only")

    def find_similars(self, description: str):
        vec = self.model.encode([description]).astype(float).tolist()
        r = self.collection.query(query_embeddings=vec, n_results=5)
        docs = r["documents"][0][:]
        prices = [m["price"] for m in r["metadatas"][0][:]]
        return docs, prices

    def _extract_price(self, s: str) -> float:
        s = s.replace("$", "").replace(",", "")
        m = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(m.group()) if m else 0.0

    def price(self, description: str) -> float:
        docs, prices = self.find_similars(description)
        context = "\n".join([f"Product: {d}\nPrice: ${p:.2f}" for d, p in zip(docs, prices)])
        msg = f"Estimate the price of this product. Respond with the price, no explanation.\n\n{description}\n\nContext:\n{context}"
        if self._client is None:
            # Fallback: use neighbor median when no LLM
            import numpy as np
            return float(np.median(prices)) if prices else 0.0
        if self._client == "litellm":
            r = __import__("litellm", fromlist=["completion"]).completion(
                model=self._model, messages=[{"role": "user", "content": msg}]
            )
            text = r.choices[0].message.content
        else:
            r = self._client.chat.completions.create(model=self._model, messages=[{"role": "user", "content": msg}])
            text = r.choices[0].message.content
        result = self._extract_price(text)
        self.log(f"Frontier Agent: ${result:.2f}")
        return result


# --- Ensemble ---
class LocalEnsembleAgent(Agent):
    name = "Ensemble Agent"
    color = Agent.YELLOW

    def __init__(self, collection):
        self.log("Initializing Ensemble Agent (specialist + frontier)")
        self.specialist = LocalSpecialistAgent()
        self.frontier = LocalFrontierAgent(collection)
        w_s = CONFIG["ENSEMBLE_SPECIALIST_W"]
        w_f = CONFIG["ENSEMBLE_FRONTIER_W"]
        self.w_s, self.w_f = w_s / (w_s + w_f), w_f / (w_s + w_f)
        self.log("Ensemble Agent ready")

    def price(self, description: str, true_price: Optional[float] = None) -> float:
        self.log("Ensemble pricing")
        s = self.specialist.price(description)
        f = self.frontier.price(description)
        result = self.w_s * s + self.w_f * f
        self.log(f"Ensemble: ${result:.2f}")
        if true_price is not None:
            err_s, err_f, err_e = abs(s - true_price), abs(f - true_price), abs(result - true_price)
            self.log(f"Accuracy (vs ${true_price:.2f}): specialist MAE=${err_s:.2f}, frontier MAE=${err_f:.2f}, ensemble MAE=${err_e:.2f}")
        return result


# --- Helper: parse JSON from LLM response (handles ```json ... ``` or raw) ---
def _parse_deal_selection_from_text(text: str) -> Optional[DealSelection]:
    """Extract JSON from LLM output and return DealSelection. Open-source models often wrap JSON in markdown."""
    if not text or not text.strip():
        return None
    text = text.strip()
    # Try ```json ... ``` first, then raw { ... }
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    raw = m.group(1).strip() if m else None
    if not raw or not raw.startswith("{"):
        m2 = re.search(r"\{[\s\S]*\}", text)
        raw = m2.group(0) if m2 else None
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "deals" in data:
            deals = []
            for d in data["deals"]:
                if not isinstance(d, dict):
                    continue
                try:
                    deal = Deal(
                        product_description=str(d.get("product_description", ""))[:500],
                        price=float(d.get("price", 0)),
                        url=str(d.get("url", "")),
                    )
                    if deal.price > 0:
                        deals.append(deal)
                except (TypeError, ValueError):
                    continue
            if deals:
                return DealSelection(deals=deals[:5])
    except (json.JSONDecodeError, TypeError, Exception):
        pass
    return None


# --- Scanner (RSS + LiteLLM for structured output; no OpenAI required) ---
class LocalScannerAgent(Agent):
    name = "Scanner Agent"
    color = Agent.CYAN

    def __init__(self):
        self.log("Initializing Scanner Agent")
        self._use_litellm = False
        try:
            __import__("litellm")
            self._use_litellm = True
            self._model = CONFIG["SCANNER_MODEL"]
            self.log(f"Scanner using LiteLLM model: {self._model}")
        except ImportError:
            self.log("litellm not installed; will use fallback parsing only")
        self.log("Scanner Agent ready")

    def fetch_deals(self, memory: List[Opportunity]) -> list:
        from agents.deals import ScrapedDeal
        urls = [o.deal.url for o in memory]
        scraped = ScrapedDeal.fetch()
        return [s for s in scraped if s.url not in urls]

    def scan(self, memory: List[Opportunity]) -> Optional[DealSelection]:
        # Mock mode for testing without API/RSS
        if os.getenv("SCANNER_USE_MOCK") == "1":
            return DealSelection(deals=[
                Deal(product_description="Hisense R6 Series 55-inch 4K UHD Roku Smart TV, Dolby Vision HDR", price=178.0, url="https://example.com/1"),
                Deal(product_description="Poly Studio P21 21.5-inch LED personal meeting display 1080p", price=30.0, url="https://example.com/2"),
            ])
        scraped = self.fetch_deals(memory)
        if not scraped:
            self.log("No new deals")
            return None
        system = "You output valid JSON only. No markdown, no explanation. Format: {\"deals\": [{\"product_description\": \"...\", \"price\": number, \"url\": \"...\"}]}. Pick the 5 best deals with clear product description and price. Price must be a number (e.g. 199.99)."
        user = "From these deals, select the 5 best with clear description and price. Output JSON with key \"deals\" and array of {\"product_description\", \"price\", \"url\"}.\n\n" + "\n\n".join([s.describe() for s in scraped[:30]])
        if self._use_litellm:
            try:
                litellm = __import__("litellm", fromlist=["completion"])
                r = litellm.completion(
                    model=self._model,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                )
                text = r.choices[0].message.content or ""
                sel = _parse_deal_selection_from_text(text)
                if sel and sel.deals:
                    self.log(f"Scanner (LiteLLM): {len(sel.deals)} deals")
                    return sel
            except Exception as e:
                logging.warning(f"Scanner LiteLLM failed: {e}; using fallback")
        # Fallback: parse $XX or XX.XX from title/summary
        deals = []
        for s in scraped[:15]:
            text = (s.title or "") + " " + (getattr(s, "summary", "") or "") + " " + (getattr(s, "details", "") or "")
            m = re.search(r"\$?\s*([\d,]+\.?\d*)", text)
            if m:
                try:
                    p = float(m.group(1).replace(",", ""))
                    if 1 < p < 10000:
                        deals.append(Deal(product_description=(s.title + " " + (getattr(s, "details", "") or ""))[:500], price=p, url=s.url))
                        if len(deals) >= 5:
                            break
                except ValueError:
                    continue
        return DealSelection(deals=deals) if deals else None


# --- Messaging (log fallback) ---
class LocalMessagingAgent(Agent):
    name = "Messaging Agent"
    color = Agent.WHITE

    def __init__(self):
        self.log("Initializing Messaging Agent")
        self.pushover_user = os.getenv("PUSHOVER_USER")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN")
        self._push_ok = bool(self.pushover_user and self.pushover_token)
        if not self._push_ok:
            self.log("Pushover not configured; will log only")
        else:
            self.log("Messaging Agent ready (Pushover)")

    def push(self, text: str):
        if self._push_ok:
            import requests
            requests.post("https://api.pushover.net/1/messages.json", data={
                "user": self.pushover_user,
                "token": self.pushover_token,
                "message": text[:500],
                "sound": "cashregister",
            })
        else:
            logging.info(f"[MESSAGING] (no Pushover) {text[:200]}")

    def alert(self, opp: Opportunity):
        text = f"Deal! ${opp.deal.price:.2f} vs est ${opp.estimate:.2f}, discount ${opp.discount:.2f}: {opp.deal.product_description[:80]}... {opp.deal.url}"
        self.push(text)
        self.log("Alert sent (or logged)")


# --- Planning Agent ---
class LocalPlanningAgent(Agent):
    name = "Planning Agent"
    color = Agent.GREEN

    def __init__(self, collection):
        self.log("Planning Agent initializing")
        self.scanner = LocalScannerAgent()
        self.ensemble = LocalEnsembleAgent(collection)
        self.messenger = LocalMessagingAgent()
        self.threshold = CONFIG["DEAL_THRESHOLD"]
        self.log("Planning Agent ready")

    def run_deal(self, deal: Deal) -> Opportunity:
        est = self.ensemble.price(deal.product_description, true_price=deal.price)
        disc = est - deal.price
        return Opportunity(deal=deal, estimate=est, discount=disc)

    def plan(self, memory: List[Opportunity]) -> Optional[Opportunity]:
        self.log("Planning run")
        sel = self.scanner.scan(memory=memory)
        if not sel or not sel.deals:
            return None
        opps = [self.run_deal(d) for d in sel.deals[:5]]
        opps.sort(key=lambda o: o.discount, reverse=True)
        best = opps[0]
        self.log(f"Best discount: ${best.discount:.2f}")
        if best.discount > self.threshold:
            self.messenger.alert(best)
            return best
        return None


# --- Framework ---
class DealAgentFramework:
    DB = "products_vectorstore"
    MEMORY_FILENAME = "memory.json"

    def __init__(self, chroma_path: Optional[Path] = None, memory_path: Optional[Path] = None):
        self.chroma_path = chroma_path or CONFIG["CHROMA_DB_PATH"]
        self.memory_path = memory_path or CONFIG["MEMORY_JSON"]
        self.memory = self._read_memory()
        import chromadb
        self.client = chromadb.PersistentClient(path=str(self.chroma_path))
        self.collection = self.client.get_or_create_collection("products")
        self.planner = None

    def _read_memory(self) -> List[Opportunity]:
        p = self.memory_path
        if not p.exists():
            return []
        with open(p) as f:
            raw = [Opportunity(**x) for x in json.load(f)]
        # Keep at most one opportunity per deal URL (best discount wins)
        by_url: dict[str, Opportunity] = {}
        for o in raw:
            url = o.deal.url
            if url not in by_url or o.discount > by_url[url].discount:
                by_url[url] = o
        deduped = list(by_url.values())
        if len(deduped) < len(raw):
            with open(p, "w") as f:
                json.dump([o.model_dump() for o in deduped], f, indent=2)
            logging.info(f"[Framework] Deduplicated memory: {len(raw)} -> {len(deduped)} entries")
        return deduped

    def _write_memory(self):
        with open(self.memory_path, "w") as f:
            json.dump([o.model_dump() for o in self.memory], f, indent=2)

    def init_agents(self):
        if self.planner is None:
            self.planner = LocalPlanningAgent(self.collection)

    def run(self) -> List[Opportunity]:
        self.init_agents()
        result = self.planner.plan(memory=self.memory)
        if result:
            seen_urls = {o.deal.url for o in self.memory}
            if result.deal.url not in seen_urls:
                self.memory.append(result)
                self._write_memory()
            else:
                logging.info(f"[Framework] Skipped duplicate deal URL: {result.deal.url[:60]}...")
        return self.memory


# --- Test hooks ---
def test_specialist():
    """Test Stage 5 specialist pricing."""
    pred = _build_stage5_predictor()
    desc = "Samsung 55 inch 4K Smart TV with HDR"
    p = pred(desc)
    print(f"test_specialist: '{desc}' -> ${p:.2f}")
    assert p > 0, "Expected positive price"


def test_frontier():
    """Test Frontier agent (requires Chroma)."""
    _ensure_chroma()
    import chromadb
    client = chromadb.PersistentClient(path=str(CONFIG["CHROMA_DB_PATH"]))
    coll = client.get_or_create_collection("products")
    agent = LocalFrontierAgent(coll)
    p = agent.price("Samsung 55 inch 4K TV")
    print(f"test_frontier: ${p:.2f}")
    assert p > 0


def test_scanner():
    """Test scanner (may use RSS; can be slow)."""
    agent = LocalScannerAgent()
    sel = agent.scan(memory=[])
    print(f"test_scanner: {len(sel.deals) if sel else 0} deals")
    if sel and sel.deals:
        print(sel.deals[0].product_description[:100])


def test_planner():
    """Test one planner cycle."""
    _ensure_chroma()
    fw = DealAgentFramework()
    fw.init_agents()
    result = fw.planner.plan(memory=[])
    print(f"test_planner: best opportunity discount = {result.discount if result else 'None'}")


def _ensure_chroma():
    p = CONFIG["CHROMA_DB_PATH"]
    if not CONFIG["SUPPORT_JSON"].exists():
        _ensure_support()  # Build from items_lite
    import chromadb
    client = chromadb.PersistentClient(path=str(p))
    coll = client.get_or_create_collection("products")
    if coll.count() == 0:
        build_chroma_from_support(p, CONFIG["SUPPORT_JSON"])


# --- Gradio UI ---
def launch_gradio():
    """Launch Gradio UI for The Price is Right."""
    import queue
    import threading
    import time
    import gradio as gr

    def table_for(opps):
        return [
            [o.deal.product_description[:80], f"${o.deal.price:.2f}", f"${o.estimate:.2f}", f"${o.discount:.2f}", o.deal.url]
            for o in opps
        ]

    class QueueHandler(logging.Handler):
        def __init__(self, q):
            super().__init__()
            self.q = q
        def emit(self, record):
            self.q.put(self.format(record))

    log_queue = queue.Queue()
    handler = QueueHandler(log_queue)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)

    fw = DealAgentFramework()

    def run_cycle(log_data, result_holder):
        fw.init_agents()
        result = fw.planner.plan(memory=fw.memory)
        if result:
            fw.memory.append(result)
            fw._write_memory()
        while not log_queue.empty():
            try:
                log_data.append(log_queue.get_nowait())
            except queue.Empty:
                break
        return log_data, table_for(fw.memory), result_holder

    with gr.Blocks(title="The Price is Right") as ui:
        log_data = gr.State([])
        logs = gr.HTML(value="<div>Run to see logs</div>")
        df = gr.Dataframe(
            headers=["Deal", "Price", "Estimate", "Discount", "URL"],
            value=table_for(fw.memory),
        )
        def do_run(lg, _):
            def worker():
                fw.run()
            t = threading.Thread(target=worker)
            t.start()
            t.join(timeout=120)
            out = []
            while not log_queue.empty():
                try:
                    out.append(log_queue.get_nowait())
                except queue.Empty:
                    break
            lg = lg + out
            html = "<br>".join(lg[-20:])
            return lg, f"<div style='height:200px;overflow:auto'>{html}</div>", table_for(fw.memory)
        btn = gr.Button("Run planner cycle")
        btn.click(do_run, [log_data, gr.State(None)], [log_data, logs, df])
        ui.load(lambda: table_for(fw.memory), None, [df])

    ui.launch(share=False, inbrowser=True)


# --- Main ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", choices=["specialist", "frontier", "scanner", "planner"], help="Run a test")
    ap.add_argument("--setup-chroma", action="store_true", help="Build Chroma from Week 7 support")
    ap.add_argument("--gradio", action="store_true", help="Launch Gradio UI")
    ap.add_argument("--run", action="store_true", help="Run one planner cycle (CLI)")
    args = ap.parse_args()
    if args.setup_chroma:
        try:
            _ensure_support()  # May build from items_lite if WEEK8_BUILD_SUPPORT=1
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)
        build_chroma_from_support(CONFIG["CHROMA_DB_PATH"], CONFIG["SUPPORT_JSON"])
        print("Chroma built.")
    elif args.test == "specialist":
        test_specialist()
    elif args.test == "frontier":
        _ensure_chroma()
        test_frontier()
    elif args.test == "scanner":
        test_scanner()
    elif args.test == "planner":
        _ensure_chroma()
        test_planner()
    elif args.gradio:
        _ensure_chroma()
        launch_gradio()
    elif args.run:
        _ensure_chroma()
        fw = DealAgentFramework()
        result = fw.run()
        print(f"Memory: {len(result)} opportunities")
    else:
        ap.print_help()
