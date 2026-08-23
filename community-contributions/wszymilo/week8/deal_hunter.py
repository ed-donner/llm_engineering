"""
Deal Hunter

Hunts for deals via RSS → scanner → ensemble pricer → notifications.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb
import feedparser
import gradio as gr
import numpy as np
import plotly.graph_objects as go
import requests
import torch
import torch.nn as nn
from bs4 import BeautifulSoup
from dotenv import load_dotenv, find_dotenv
from litellm import completion
from openai import OpenAI
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.manifold import TSNE

load_dotenv(find_dotenv(), override=True)

# -----------------------------------------------------------------------------
# 1. Config
# -----------------------------------------------------------------------------

_EXERCISE_DIR = Path(__file__).resolve().parent
_WEEK8_DIR = _EXERCISE_DIR.parent


@dataclass
class Config:
    """Central config for paths, thresholds, and weights."""

    db_path: str = str(_WEEK8_DIR / "products_vectorstore")
    memory_path: str = str(_EXERCISE_DIR / "memory.json")
    nn_weights_path: str = str(_WEEK8_DIR / "deep_neural_network.pth")
    collection_name: str = "products"
    deal_threshold: float = 50.0
    weight_frontier: float = 0.8
    weight_specialist: float = 0.1
    weight_nn: float = 0.1
    scanner_model: str = "gpt-5-nano"
    frontier_model: str = "gpt-5-nano"
    preprocessor_model: str = "gpt-5-nano"
    timer_interval_sec: float = 300.0
    plot_max_datapoints: int = 800
    log_buffer_max: int = 500
    rss_fetch_parallel: int = 8


# Plot categories and colors (must match vectorstore metadata)
PLOT_CATEGORIES = [
    "Appliances",
    "Automotive",
    "Cell_Phones_and_Accessories",
    "Electronics",
    "Musical_Instruments",
    "Office_Products",
    "Tools_and_Home_Improvement",
    "Toys_and_Games",
]
PLOT_COLORS = ["red", "blue", "brown", "orange", "yellow", "green", "purple", "cyan"]

RSS_FEEDS = [
    "https://www.dealnews.com/c142/Electronics/?rss=1",
    "https://www.dealnews.com/c39/Computers/?rss=1",
    "https://www.dealnews.com/f1912/Smart-Home/?rss=1",
]

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

# -----------------------------------------------------------------------------
# 2. Data models (Pydantic)
# -----------------------------------------------------------------------------


class Deal(BaseModel):
    """Deal with product description, price, and URL."""

    product_description: str = Field(
        description="Your clearly expressed summary of the product in 3-4 sentences."
    )
    price: float = Field(description="The actual price of this product, as advertised.")
    url: str = Field(description="The URL of the deal, as provided in the input.")


class DealSelection(BaseModel):
    """Selection of up to 5 deals from the scanner."""

    deals: List[Deal] = Field(
        description="Your selection of the 5 deals with the most detailed description and clear price."
    )


class Opportunity(BaseModel):
    """Priced opportunity: deal plus estimate and discount."""

    deal: Deal
    estimate: float
    discount: float


# -----------------------------------------------------------------------------
# 3. Logging and HTML
# -----------------------------------------------------------------------------

# ANSI → HTML color mapping for log display
_BG_BLACK = "\033[40m"
_BG_BLUE = "\033[44m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_BLUE = "\033[34m"
_MAGENTA = "\033[35m"
_CYAN = "\033[36m"
_WHITE = "\033[37m"
_RESET = "\033[0m"

_LOG_MAPPER = {
    _BG_BLACK + _RED: "#dd0000",
    _BG_BLACK + _GREEN: "#00dd00",
    _BG_BLACK + _YELLOW: "#dddd00",
    _BG_BLACK + _BLUE: "#0000ee",
    _BG_BLACK + _MAGENTA: "#aa00dd",
    _BG_BLACK + _CYAN: "#00dddd",
    _BG_BLACK + _WHITE: "#87CEEB",
    _BG_BLUE + _WHITE: "#ff7800",
}


def _log_reformat(message: str) -> str:
    """Convert ANSI-colored log message to HTML spans."""
    for code, color in _LOG_MAPPER.items():
        message = message.replace(code, f'<span style="color: {color}">')
    return message.replace(_RESET, "</span>")


class _QueueHandler(logging.Handler):
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self._queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        self._queue.put(self.format(record))


def _setup_ui_logging(log_queue: queue.Queue) -> None:
    handler = _QueueHandler(log_queue)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S %z")
    )
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def _html_for_log(log_lines: List[str], max_lines: int = 18) -> str:
    lines = log_lines[-max_lines:]
    body = "<br>".join(lines)
    return f'<div style="height: 400px; overflow-y: auto; border: 1px solid #ccc; background-color: #222229; padding: 10px;">{body}</div>'


def agent_log(name: str, color: str, message: str) -> None:
    """Emit a colored log line for an agent (replaces Agent base class)."""
    text = _WHITE + color + f"[{name}] {message}" + _RESET
    logging.info(text)


# -----------------------------------------------------------------------------
# 4. RSS and scraping
# -----------------------------------------------------------------------------


def _extract_summary(html_snippet: str) -> str:
    soup = BeautifulSoup(html_snippet, "html.parser")
    div = soup.find("div", class_="snippet summary")
    if div:
        desc = div.get_text(strip=True)
        desc = BeautifulSoup(desc, "html.parser").get_text()
        desc = re.sub("<[^<]+?>", "", desc)
        result = desc.strip()
    else:
        result = html_snippet
    return result.replace("\n", " ")


class ScrapedDeal:
    """Deal scraped from an RSS entry (fetches page for details)."""

    def __init__(self, entry: Dict[str, Any]) -> None:
        self.title = entry["title"]
        self.summary = _extract_summary(entry["summary"])
        self.url = entry["links"][0]["href"]
        resp = requests.get(self.url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")
        content_div = soup.find("div", class_="content-section")
        content = content_div.get_text() if content_div else ""
        content = content.replace("\nmore", "").replace("\n", " ")
        if "Features" in content:
            self.details, self.features = content.split("Features", 1)
        else:
            self.details = content
            self.features = ""
        self._truncate()

    def _truncate(self) -> None:
        self.title = self.title[:100]
        self.details = self.details[:500]
        self.features = self.features[:500]

    def describe(self) -> str:
        return f"Title: {self.title}\nDetails: {self.details.strip()}\nFeatures: {self.features.strip()}\nURL: {self.url}"


def _fetch_scraped_deals_parallel(
    feeds: List[str], max_per_feed: int = 10, max_workers: int = 8
) -> List[ScrapedDeal]:
    """Fetch deals from RSS feeds; fetch each deal page in parallel."""
    entries: List[Dict[str, Any]] = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_per_feed]:
            entries.append(entry)

    def build_one(entry: Dict[str, Any]) -> Optional[ScrapedDeal]:
        try:
            return ScrapedDeal(entry)
        except Exception:
            return None

    deals: List[ScrapedDeal] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for obj in executor.map(build_one, entries):
            if obj is not None:
                deals.append(obj)
    return deals


# -----------------------------------------------------------------------------
# 5. Scanner (RSS → OpenAI structured output → DealSelection)
# -----------------------------------------------------------------------------

SCANNER_SYSTEM = """You identify and summarize the 5 most detailed deals from a list, by selecting deals that have the most detailed, high quality description and the most clear price.
Respond strictly in JSON with no explanation. Provide the price as a number. If the price of a deal isn't clear, do not include that deal.
Be careful with products described as "$XXX off" or "reduced by $XXX" - that is not the actual price. Only include products when you are highly confident about the price."""

SCANNER_USER_PREFIX = """Respond with the most promising 5 deals from this list, with the most detailed product description and a clear price greater than 0.
Rephrase the description to be a summary of the product itself, not the terms of the deal.
Deals:

"""

SCANNER_USER_SUFFIX = "\n\nInclude exactly 5 deals, no more."


class DealScanner:
    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self._client = OpenAI()
        agent_log("DealScanner", _CYAN, "initialized")

    def _fetch_new_deals(self, memory: List[Opportunity]) -> List[ScrapedDeal]:
        urls = {opp.deal.url for opp in memory}
        all_deals = _fetch_scraped_deals_parallel(
            RSS_FEEDS, max_workers=self._cfg.rss_fetch_parallel
        )
        new_deals = [d for d in all_deals if d.url not in urls]
        agent_log("DealScanner", _CYAN, f"received {len(new_deals)} deals not already in memory")
        return new_deals

    def scan(self, memory: List[Opportunity]) -> Optional[DealSelection]:
        scraped = self._fetch_new_deals(memory)
        if not scraped:
            return None
        user_content = SCANNER_USER_PREFIX + "\n\n".join(d.describe() for d in scraped) + SCANNER_USER_SUFFIX
        agent_log("DealScanner", _CYAN, "calling OpenAI with structured output")
        resp = self._client.chat.completions.parse(
            model=self._cfg.scanner_model,
            messages=[
                {"role": "system", "content": SCANNER_SYSTEM},
                {"role": "user", "content": user_content},
            ],
            response_format=DealSelection,
            reasoning_effort="minimal",
        )
        selection = resp.choices[0].message.parsed
        selection.deals = [d for d in selection.deals if d.price > 0]
        agent_log("DealScanner", _CYAN, f"received {len(selection.deals)} deals with price>0")
        return selection


# -----------------------------------------------------------------------------
# 6. Preprocessor
# -----------------------------------------------------------------------------

PREPROCESSOR_SYSTEM = """Create a concise description of a product. Respond only in this format. Do not include part numbers.
Title: Rewritten short precise title
Category: eg Electronics
Brand: Brand name
Description: 1 sentence description
Details: 1 sentence on features"""


class TextPreprocessor:
    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self._model = cfg.preprocessor_model
        self._reasoning = "low" if "gpt-oss" in self._model else None
        self._base_url = None
        if "ollama" in self._model:
            self._base_url = "http://localhost:11434"

    def preprocess(self, text: str) -> str:
        messages = [
            {"role": "system", "content": PREPROCESSOR_SYSTEM},
            {"role": "user", "content": text},
        ]
        response = completion(
            messages=messages,
            model=self._model,
            reasoning_effort=self._reasoning,
            api_base=self._base_url,
        )
        return response.choices[0].message.content


# -----------------------------------------------------------------------------
# 7. Frontier (Chroma RAG + OpenAI)
# -----------------------------------------------------------------------------


class FrontierPricer:
    def __init__(self, collection: Any, cfg: Config) -> None:
        self._collection = collection
        self._cfg = cfg
        self._client = OpenAI()
        self._encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        agent_log("FrontierPricer", _BLUE, "ready")

    def _find_similars(self, description: str) -> Tuple[List[str], List[float]]:
        agent_log("FrontierPricer", _BLUE, "RAG search for 5 similar products")
        vec = self._encoder.encode([description])
        result = self._collection.query(
            query_embeddings=vec.astype(float).tolist(), n_results=5
        )
        docs = result["documents"][0][:]
        prices = [m["price"] for m in result["metadatas"][0][:]]
        return docs, prices

    @staticmethod
    def _parse_price(s: str) -> float:
        s = s.replace("$", "").replace(",", "")
        m = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(m.group()) if m else 0.0

    def estimate(self, description: str) -> float:
        docs, prices = self._find_similars(description)
        agent_log("FrontierPricer", _BLUE, f"calling {self._cfg.frontier_model} with 5 similar products")
        msg = f"Estimate the price of this product. Respond with the price, no explanation\n\n{description}\n\n"
        msg += "To provide some context, here are similar items:\n\n"
        for d, p in zip(docs, prices):
            msg += f"Potentially related product:\n{d}\nPrice is ${p:.2f}\n\n"
        response = self._client.chat.completions.create(
            model=self._cfg.frontier_model,
            messages=[{"role": "user", "content": msg}],
            seed=42,
            reasoning_effort="minimal",
        )
        reply = response.choices[0].message.content or ""
        price = self._parse_price(reply)
        agent_log("FrontierPricer", _BLUE, f"predicting ${price:.2f}")
        return price


# -----------------------------------------------------------------------------
# 8. Specialist (Modal Pricer)
# -----------------------------------------------------------------------------


class SpecialistPricer:
    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        import modal
        Pricer = modal.Cls.from_name("pricer-service", "Pricer")
        self._pricer = Pricer()
        agent_log("SpecialistPricer", _RED, "connected to Modal")

    def estimate(self, description: str) -> float:
        agent_log("SpecialistPricer", _RED, "calling remote fine-tuned model")
        result = self._pricer.price.remote(description)
        agent_log("SpecialistPricer", _RED, f"predicting ${result:.2f}")
        return result


# -----------------------------------------------------------------------------
# 9. Deep NN
# -----------------------------------------------------------------------------

# Values shown by Ed upon training the Net.
DNN_Y_STD = 1.0328539609909058
DNN_Y_MEAN = 4.434937953948975


class _ResidualBlock(nn.Module):
    def __init__(self, hidden_size: int, dropout_prob: float) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout_prob),
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size),
        )
        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.relu(self.block(x) + x)


class _DeepNN(nn.Module):
    def __init__(
        self,
        input_size: int,
        num_layers: int = 10,
        hidden_size: int = 4096,
        dropout_prob: float = 0.2,
    ) -> None:
        super().__init__()
        self.input_layer = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout_prob),
        )
        self.residual_blocks = nn.ModuleList([
            _ResidualBlock(hidden_size, dropout_prob) for _ in range(num_layers - 2)
        ])
        self.output_layer = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_layer(x)
        for block in self.residual_blocks:
            x = block(x)
        return self.output_layer(x)


class NeuralPricer:
    def __init__(self, weights_path: str) -> None:
        self._path = weights_path
        self._vectorizer: Optional[Any] = None
        self._model: Optional[_DeepNN] = None
        self._device: Optional[torch.device] = None

    def _setup(self) -> None:
        if self._model is not None:
            return
        np.random.seed(42)
        torch.manual_seed(42)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(42)
        self._vectorizer = HashingVectorizer(n_features=5000, stop_words="english", binary=True)
        self._model = _DeepNN(5000)
        if torch.cuda.is_available():
            self._device = torch.device("cuda")
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            self._device = torch.device("mps")
        else:
            self._device = torch.device("cpu")
        logging.info(f"NeuralPricer using {self._device}")
        self._model.to(self._device)
        self._model.load_state_dict(torch.load(self._path, map_location=self._device))

    def estimate(self, text: str) -> float:
        self._setup()
        assert self._model is not None and self._vectorizer is not None
        self._model.eval()
        with torch.no_grad():
            vec = self._vectorizer.transform([text])
            vec_t = torch.FloatTensor(vec.toarray()).to(self._device)
            pred = self._model(vec_t)[0]
            result = torch.exp(pred * DNN_Y_STD + DNN_Y_MEAN).item() - 1
        return max(0.0, result)


# -----------------------------------------------------------------------------
# 10. Ensemble (parallel specialist + frontier + NN)
# -----------------------------------------------------------------------------


class EnsemblePricer:
    def __init__(self, collection: Any, cfg: Config) -> None:
        self._cfg = cfg
        self._preprocessor = TextPreprocessor(cfg)
        self._frontier = FrontierPricer(collection, cfg)
        self._specialist = SpecialistPricer(cfg)
        self._nn = NeuralPricer(cfg.nn_weights_path)
        agent_log("EnsemblePricer", _YELLOW, "ready")

    def estimate(self, description: str) -> float:
        agent_log("EnsemblePricer", _YELLOW, "preprocessing text")
        rewritten = self._preprocessor.preprocess(description)
        agent_log("EnsemblePricer", _YELLOW, f"preprocessed with {self._cfg.preprocessor_model}")

        def run_specialist() -> float:
            return self._specialist.estimate(rewritten)

        def run_frontier() -> float:
            return self._frontier.estimate(rewritten)

        def run_nn() -> float:
            agent_log("NeuralPricer", _MAGENTA, "starting prediction")
            r = self._nn.estimate(rewritten)
            agent_log("NeuralPricer", _MAGENTA, f"predicting ${r:.2f}")
            return r

        with ThreadPoolExecutor(max_workers=3) as ex:
            fut_s = ex.submit(run_specialist)
            fut_f = ex.submit(run_frontier)
            fut_n = ex.submit(run_nn)
            specialist = fut_s.result()
            frontier = fut_f.result()
            nn_val = fut_n.result()

        combined = (
            frontier * self._cfg.weight_frontier
            + specialist * self._cfg.weight_specialist
            + nn_val * self._cfg.weight_nn
        )
        agent_log("EnsemblePricer", _YELLOW, f"combined estimate ${combined:.2f}")
        return combined


# -----------------------------------------------------------------------------
# 11. Messaging (Pushover)
# -----------------------------------------------------------------------------


class Notifier:
    def __init__(self) -> None:
        self._user = os.getenv("PUSHOVER_USER", "your-pushover-user-if-not-using-env")
        self._token = os.getenv("PUSHOVER_TOKEN", "your-pushover-token-if-not-using-env")
        agent_log("Notifier", _WHITE, "initialized Pushover")

    def alert(self, opportunity: Opportunity) -> None:
        text = (
            f"Deal Alert! Price=${opportunity.deal.price:.2f}, "
            f"Estimate=${opportunity.estimate:.2f}, "
            f"Discount=${opportunity.discount:.2f} : "
            f"{opportunity.deal.product_description[:10]}... "
            f"{opportunity.deal.url}"
        )
        self._push(text)
        agent_log("Notifier", _WHITE, "alert sent")

    def _push(self, text: str) -> None:
        requests.post(
            PUSHOVER_URL,
            data={
                "user": self._user,
                "token": self._token,
                "message": text,
                "sound": "cashregister",
            },
            timeout=10,
        )


# -----------------------------------------------------------------------------
# 12. Orchestrator (scan → select → preprocess → ensemble → threshold → notify)
# -----------------------------------------------------------------------------


class DealOrchestrator:
    def __init__(self, collection: Any, cfg: Config) -> None:
        self._cfg = cfg
        self._scanner = DealScanner(cfg)
        self._ensemble = EnsemblePricer(collection, cfg)
        self._notifier = Notifier()
        agent_log("DealOrchestrator", _GREEN, "ready")

    def run_cycle(self, memory: List[Opportunity]) -> Optional[Opportunity]:
        agent_log("DealOrchestrator", _GREEN, "starting run")
        selection = self._scanner.scan(memory)
        if not selection or not selection.deals:
            return None
        opportunities = []
        for deal in selection.deals[:5]:
            estimate = self._ensemble.estimate(deal.product_description)
            discount = estimate - deal.price
            opportunities.append(Opportunity(deal=deal, estimate=estimate, discount=discount))
        opportunities.sort(key=lambda o: o.discount, reverse=True)
        best = opportunities[0]
        agent_log("DealOrchestrator", _GREEN, f"best deal discount ${best.discount:.2f}")
        if best.discount > self._cfg.deal_threshold:
            self._notifier.alert(best)
        agent_log("DealOrchestrator", _GREEN, "run complete")
        return best if best.discount > self._cfg.deal_threshold else None


# -----------------------------------------------------------------------------
# 13. Pipeline (Chroma, memory, run, plot with TSNE cache)
# -----------------------------------------------------------------------------


def _init_console_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not root.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(
            logging.Formatter(
                "[%(asctime)s] [Agents] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S %z",
            )
        )
        root.addHandler(h)


class DealPipeline:
    def __init__(self, cfg: Optional[Config] = None) -> None:
        self._cfg = cfg or Config()
        _init_console_logging()
        self._client = chromadb.PersistentClient(path=self._cfg.db_path)
        self._collection = self._client.get_or_create_collection(self._cfg.collection_name)
        self._memory = self._load_memory()
        self._orchestrator: Optional[DealOrchestrator] = None
        self._tsne_cache: Optional[Tuple[List[str], np.ndarray, List[str]]] = None
        self._tsne_cache_key: Optional[Tuple[str, int]] = None

    def _load_memory(self) -> List[Opportunity]:
        path = self._cfg.memory_path
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Opportunity(**item) for item in data]

    def _save_memory(self) -> None:
        path = self._cfg.memory_path
        data = [o.model_dump() for o in self._memory]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _get_orchestrator(self) -> DealOrchestrator:
        if self._orchestrator is None:
            agent_log("DealPipeline", _BG_BLUE + _WHITE, "initializing pipeline")
            self._orchestrator = DealOrchestrator(self._collection, self._cfg)
            agent_log("DealPipeline", _BG_BLUE + _WHITE, "pipeline ready")
        return self._orchestrator

    def execute(self) -> List[Opportunity]:
        orch = self._get_orchestrator()
        logging.info("Kicking off DealOrchestrator")
        result = orch.run_cycle(self._memory)
        logging.info(f"DealOrchestrator returned: {result}")
        if result is not None:
            self._memory.append(result)
            self._save_memory()
        return self._memory

    def get_plot_data(self, max_datapoints: Optional[int] = None) -> Tuple[List[str], np.ndarray, List[str]]:
        max_pts = max_datapoints or self._cfg.plot_max_datapoints
        key = (self._cfg.db_path, max_pts)
        if self._tsne_cache_key == key and self._tsne_cache is not None:
            return self._tsne_cache
        result = self._collection.get(
            include=["embeddings", "documents", "metadatas"],
            limit=max_pts,
        )
        vectors = np.array(result["embeddings"])
        documents = result["documents"]
        categories = [m["category"] for m in result["metadatas"]]
        colors = [PLOT_COLORS[PLOT_CATEGORIES.index(c)] for c in categories]
        tsne = TSNE(n_components=3, random_state=42, n_jobs=-1)
        reduced = tsne.fit_transform(vectors)
        self._tsne_cache = (documents, reduced, colors)
        self._tsne_cache_key = key
        return self._tsne_cache

    @property
    def memory(self) -> List[Opportunity]:
        return self._memory


# -----------------------------------------------------------------------------
# 14. UI (Gradio)
# -----------------------------------------------------------------------------

UI_TITLE = "The Price is Right"
UI_SUBTITLE = "Autonomous Agent Framework that hunts for deals"
UI_DESCRIPTION = "A proprietary fine-tuned LLM deployed on Modal and a RAG pipeline with a frontier model collaborate to send push notifications with great online deals."
TABLE_HEADERS = ["Deals found so far", "Price", "Estimate", "Discount", "URL"]


def _table_rows(opportunities: List[Opportunity]) -> List[List[Any]]:
    return [
        [
            opp.deal.product_description,
            f"${opp.deal.price:.2f}",
            f"${opp.estimate:.2f}",
            f"${opp.discount:.2f}",
            opp.deal.url,
        ]
        for opp in opportunities
    ]


def _update_output(
    log_data: List[str],
    log_queue: queue.Queue,
    result_queue: queue.Queue,
    pipeline: DealPipeline,
    max_log_lines: int = 18,
) -> Any:
    initial = _table_rows(pipeline.memory)
    final_result = None
    while True:
        try:
            msg = log_queue.get_nowait()
            log_data.append(_log_reformat(msg))
            if len(log_data) > 500:
                log_data[:] = log_data[-500:]
            yield log_data, _html_for_log(log_data, max_log_lines), final_result or initial
        except queue.Empty:
            try:
                final_result = result_queue.get_nowait()
                yield log_data, _html_for_log(log_data, max_log_lines), final_result or initial
            except queue.Empty:
                if final_result is not None:
                    break
                time.sleep(0.1)


def _make_plot_placeholder(title: str = "Loading vector DB...") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(title=title, height=400)
    return fig


def _make_tsne_plot(documents: List[str], vectors: np.ndarray, colors: List[str]) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=vectors[:, 0],
                y=vectors[:, 1],
                z=vectors[:, 2],
                mode="markers",
                marker=dict(size=2, color=colors, opacity=0.7),
            )
        ]
    )
    fig.update_layout(
        scene=dict(
            xaxis_title="x",
            yaxis_title="y",
            zaxis_title="z",
            aspectmode="manual",
            aspectratio=dict(x=2.2, y=2.2, z=1),
            camera=dict(eye=dict(x=1.6, y=1.6, z=0.8)),
        ),
        height=400,
        margin=dict(r=5, b=1, l=5, t=2),
    )
    return fig


def build_ui(pipeline: DealPipeline, cfg: Optional[Config] = None) -> None:
    cfg = cfg or pipeline._cfg

    with gr.Blocks(title=UI_TITLE, fill_width=True) as ui:
        log_data = gr.State([])

        def do_run() -> List[List[Any]]:
            opportunities = pipeline.execute()
            return _table_rows(opportunities)

        def run_with_logging(initial_log_data: List[str]):
            log_queue: queue.Queue = queue.Queue()
            result_queue: queue.Queue = queue.Queue()
            _setup_ui_logging(log_queue)

            def worker() -> None:
                result_queue.put(do_run())

            t = threading.Thread(target=worker)
            t.start()

            for ld, html, table in _update_output(
                initial_log_data, log_queue, result_queue, pipeline
            ):
                yield ld, html, table

        def get_plot():
            try:
                docs, vecs, colors = pipeline.get_plot_data(max_datapoints=cfg.plot_max_datapoints)
                return _make_tsne_plot(docs, vecs, colors)
            except Exception:
                return _make_plot_placeholder("Error loading plot data")

        def on_select(evt: gr.SelectData) -> None:
            row = evt.index[0]
            opportunities = pipeline.memory
            if 0 <= row < len(opportunities):
                pipeline._get_orchestrator()._notifier.alert(opportunities[row])

        with gr.Row():
            gr.Markdown(f'<div style="text-align: center; font-size: 24px"><strong>{UI_TITLE}</strong> - {UI_SUBTITLE}</div>')
        with gr.Row():
            gr.Markdown(f'<div style="text-align: center; font-size: 14px">{UI_DESCRIPTION}</div>')
        with gr.Row():
            opportunities_df = gr.Dataframe(
                headers=TABLE_HEADERS,
                wrap=True,
                column_widths=[6, 1, 1, 1, 3],
                row_count=10,
                col_count=5,
                max_height=400,
            )
        with gr.Row():
            with gr.Column(scale=1):
                logs_html = gr.HTML()
            with gr.Column(scale=1):
                plot = gr.Plot(value=get_plot(), show_label=False)

        ui.load(
            run_with_logging,
            inputs=[log_data],
            outputs=[log_data, logs_html, opportunities_df],
        )
        timer = gr.Timer(value=cfg.timer_interval_sec, active=True)
        timer.tick(
            run_with_logging,
            inputs=[log_data],
            outputs=[log_data, logs_html, opportunities_df],
        )
        opportunities_df.select(on_select)

    ui.launch(share=False, inbrowser=True)


def main() -> None:
    load_dotenv(find_dotenv(), override=True)
    cfg = Config()
    pipeline = DealPipeline(cfg)
    build_ui(pipeline, cfg)


if __name__ == "__main__":
    main()
