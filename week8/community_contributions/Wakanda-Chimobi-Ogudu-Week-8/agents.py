import os
import re
from dataclasses import dataclass, field
from typing import Any, List, Optional

from agent_framework import AgentLogger, DealMemory, init_logging


@dataclass
class Deal:
    product_description: str
    price: float
    url: str


@dataclass
class DealSelection:
    deals: List[Deal] = field(default_factory=list)


@dataclass
class Opportunity:
    deal: Deal
    estimate: float
    discount: float


class ScannerAgent:
    """Subscribes to RSS feeds and identifies appetizing bargains worth exploring."""

    def __init__(self, feed_urls: Optional[List[str]] = None):
        self.logger = AgentLogger("Scanner")
        self.feed_urls = feed_urls or [
            "https://www.dealnews.com/c142/Electronics/?rss=1",
            "https://www.dealnews.com/c39/Computers/?rss=1",
        ]

    def fetch_deals(self, memory: DealMemory, max_per_feed: int = 10) -> List[Any]:
        try:
            import feedparser
        except ImportError:
            self.logger.info("feedparser not installed; returning empty list")
            return []
        all_entries = []
        for url in self.feed_urls:
            try:
                feed = feedparser.parse(url)
                for e in feed.entries[:max_per_feed]:
                    link = (e.get("links") or [{}])[0].get("href", "")
                    if link and not memory.seen(link):
                        all_entries.append(
                            {
                                "title": (e.get("title") or "")[:200],
                                "summary": (e.get("summary", "") or "")[:500],
                                "url": link,
                            }
                        )
            except Exception as ex:
                self.logger.error("RSS fetch failed", url=url, error=str(ex))
        return all_entries

    def _extract_reasonable_price(self, price_text: str, url: str, description: str) -> Optional[float]:
        """Extract a price in plausible range (1–5000) from text/url when LLM returns an ID or wrong number."""
        # URL pattern e.g. "for-616-00" or "-999-99"
        m = re.search(r"for-(\d+)-(\d+)", url, re.IGNORECASE)
        if m:
            p = float(m.group(1)) + float(m.group(2)) / 100.0
            if 1 <= p <= 5000:
                return p
        # All numbers in price_text or description; pick one in [1, 5000]
        for s in (price_text, description):
            for m in re.finditer(r"\$?\s*(\d{1,4}(?:\.\d{2})?)", s.replace(",", "")):
                p = float(m.group(1))
                if 1 <= p <= 5000:
                    return p
        return None

    def select_bargains(self, entries: List[Any], top_k: int = 5) -> DealSelection:
        """Pick top_k entries as potential bargains. If litellm available, use LLM to pick; else by length/price hint."""
        if not entries:
            return DealSelection(deals=[])
        try:
            from litellm import completion
            prompt = "From these deals, pick up to %d that look like clear product descriptions with a price. For each, reply with one line: description (short) | price number | url. One line per deal, no other text.\n\n" % top_k
            for i, e in enumerate(entries[:30]):
                prompt += f"{i+1}. {e.get('title','')} | {e.get('summary','')[:200]} | {e.get('url','')}\n"
            resp = completion(
                model=os.getenv("FRONTIER_MODEL", "openrouter/openai/gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                api_key=os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"),
            )
            text = (resp.choices[0].message.content or "").strip()
            deals = []
            for line in text.split("\n"):
                line = line.strip()
                if not line or "|" not in line:
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    desc, price_s, url = parts[0], parts[1], parts[2]
                    m = re.search(r"[-+]?\d*\.?\d+", price_s.replace("$", "").replace(",", ""))
                    price = float(m.group()) if m else 0.0
                    # Sanity check: LLM sometimes returns IDs or huge numbers; prefer price-like values
                    if price > 5000:
                        fallback = self._extract_reasonable_price(price_s, url, desc)
                        if fallback and 0 < fallback <= 5000:
                            price = fallback
                    if price > 0 and url.startswith("http"):
                        deals.append(Deal(product_description=desc, price=price, url=url))
            return DealSelection(deals=deals[:top_k])
        except Exception as ex:
            self.logger.info("LLM selection failed, using first entries", error=str(ex))
            deals = []
            for e in entries[:top_k]:
                price_s = e.get("summary", "") or e.get("title", "")
                m = re.search(r"\$?\s*(\d+\.?\d*)", price_s)
                price = float(m.group(1)) if m else 99.0
                deals.append(
                    Deal(
                        product_description=(e.get("title") or "") + " " + (e.get("summary") or "")[:300],
                        price=price,
                        url=e.get("url", ""),
                    )
                )
            return DealSelection(deals=deals)

    def scan(self, memory: DealMemory) -> Optional[DealSelection]:
        entries = self.fetch_deals(memory)
        if not entries:
            return None
        return self.select_bargains(entries)



class SpecialistAgent:
    """Calls fine-tuned LLM deployed on Modal"""

    def __init__(self):
        self.logger = AgentLogger("Specialist")
        self._pricer = None

    def _get_pricer(self):
        if self._pricer is None:
            try:
                import modal
                Pricer = modal.Cls.from_name("wakanda-pricer-service", "SpecialistPricer")
                self._pricer = Pricer()
            except Exception as e:
                self.logger.error("Modal SpecialistPricer unavailable", error=str(e))
        return self._pricer

    def price(self, description: str) -> float:
        p = self._get_pricer()
        if p is None:
            return 0.0
        try:
            out = p.price.remote(description)
            self.logger.info("Specialist estimate", value=out)
            return float(out)
        except Exception as e:
            self.logger.error("Specialist call failed", error=str(e))
            return 0.0


class FrontierAgent:
    """Estimates price using frontier model + RAG"""

    def __init__(self, collection=None):
        self.logger = AgentLogger("Frontier")
        self.collection = collection
        self._encoder = None

    def _encoder_model(self):
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            except ImportError:
                self.logger.info("sentence_transformers not installed; RAG context will be empty")
        return self._encoder

    def find_similars(self, description: str, n: int = 5) -> tuple:
        if self.collection is None:
            return [], []
        enc = self._encoder_model()
        if enc is None:
            return [], []
        try:
            vec = enc.encode([description])
            r = self.collection.query(query_embeddings=vec.tolist(), n_results=n)
            docs = (r.get("documents") or [[]])[0]
            metas = (r.get("metadatas") or [[]])[0]
            prices = [m.get("price", 0.0) for m in metas]
            return docs, prices
        except Exception as e:
            self.logger.error("RAG search failed", error=str(e))
            return [], []

    def price(self, description: str) -> float:
        similars, prices = self.find_similars(description)
        try:
            from litellm import completion
            context = ""
            for d, p in zip(similars, prices):
                context += f"Similar: {d[:200]}\nPrice: ${p:.2f}\n\n"
            prompt = f"Estimate the price in USD. Reply with only the number.\n\n{description}\n\n"
            if context:
                prompt += "Context:\n" + context
            resp = completion(
                model=os.getenv("FRONTIER_MODEL", "openrouter/openai/gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                api_key=os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"),
            )
            text = (resp.choices[0].message.content or "").strip()
            s = text.replace("$", "").replace(",", "")
            m = re.search(r"[-+]?\d*\.?\d+", s)
            return max(0.0, float(m.group())) if m else 0.0
        except Exception as e:
            self.logger.error("Frontier call failed", error=str(e))
            return 0.0


class NeuralNetworkAgent:
    """Simple regression estimate (TF-IDF + Ridge)"""

    def __init__(self, fallback_mean: float = 50.0):
        self.logger = AgentLogger("NeuralNet")
        self.fallback_mean = fallback_mean
        self._model = None
        self._vectorizer = None

    def price(self, description: str) -> float:
        if self._model is None:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.linear_model import Ridge
                self._vectorizer = TfidfVectorizer(max_features=2000, stop_words="english")
                self._model = Ridge(alpha=1.0)
                self._vectorizer.fit([description or "product"])
                X = self._vectorizer.transform([description or "product"])
                self._model.fit(X, [self.fallback_mean])
            except ImportError:
                return self.fallback_mean
        try:
            X = self._vectorizer.transform([description or "product"])
            out = self._model.predict(X)[0]
            return max(0.0, float(out))
        except Exception:
            return self.fallback_mean


class EnsembleAgent:
    """Combines Specialist (fine-tuned), Frontier (RAG), Neural estimates."""

    def __init__(self, collection=None, weights: Optional[tuple] = None):
        self.logger = AgentLogger("Ensemble")
        # Default: frontier 0.5, specialist 0.35, neural 0.15
        self.weights = weights or (0.5, 0.35, 0.15)
        self.specialist = SpecialistAgent()
        self.frontier = FrontierAgent(collection)
        self.neural = NeuralNetworkAgent()

    def price(self, description: str) -> float:
        s = self.specialist.price(description)
        f = self.frontier.price(description)
        n = self.neural.price(description)
        w1, w2, w3 = self.weights
        combined = w1 * f + w2 * s + w3 * n
        self.logger.info("Ensemble", specialist=s, frontier=f, neural=n, combined=combined)
        return combined


class MessagingAgent:
    """Drafts message with LLM and sends push notification (Telegram or Pushover) for great opportunities."""

    TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self):
        self.logger = AgentLogger("Messaging")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        self.pushover_user = os.getenv("PUSHOVER_USER", "")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN", "")

    def craft_message(self, opportunity: Opportunity) -> str:
        try:
            from litellm import completion
            prompt = (
                "Write a short, exciting 2–3 sentence push notification for this deal. "
                "Include: item summary, deal price, estimated value, and why it's a good opportunity. "
                "No hashtags. Only the message text.\n\n"
                f"Description: {opportunity.deal.product_description[:400]}\n"
                f"Deal price: ${opportunity.deal.price:.2f}\n"
                f"Estimated value: ${opportunity.estimate:.2f}\n"
                f"Discount: ${opportunity.discount:.2f}\n"
                f"URL: {opportunity.deal.url}"
            )
            resp = completion(
                model=os.getenv("MESSAGING_MODEL", "openrouter/openai/gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                api_key=os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"),
            )
            body = (resp.choices[0].message.content or "").strip()[:500]
        except Exception as e:
            self.logger.error("Draft message failed", error=str(e))
            body = (
                f"Deal! {opportunity.deal.product_description[:80]}... "
                f"Price ${opportunity.deal.price:.2f}, est. ${opportunity.estimate:.2f}, "
                f"save ${opportunity.discount:.2f}."
            )
        if opportunity.deal.url:
            body = f"{body}\n\nLink: {opportunity.deal.url}"
        return body

    def push(self, text: str, deal_url: Optional[str] = None) -> bool:
        import requests
        msg = text[:4096]  # Telegram limit 4096
        if deal_url and deal_url not in msg:
            msg = f"{msg.strip()}\n\nLink: {deal_url}"
        # Prefer Telegram if configured
        if self.telegram_token and self.telegram_chat_id:
            try:
                url = self.TELEGRAM_API.format(token=self.telegram_token)
                r = requests.post(
                    url,
                    json={"chat_id": self.telegram_chat_id, "text": msg, "disable_web_page_preview": True},
                    timeout=10,
                )
                r.raise_for_status()
                self.logger.info("Telegram notification sent")
                return True
            except Exception as e:
                self.logger.error("Telegram push failed", error=str(e))
                return False
        if self.pushover_user and self.pushover_token:
            try:
                requests.post(
                    "https://api.pushover.net/1/messages.json",
                    data={"user": self.pushover_user, "token": self.pushover_token, "message": msg[:1024], "sound": "cashregister"},
                    timeout=10,
                )
                self.logger.info("Pushover notification sent")
                return True
            except Exception as e:
                self.logger.error("Pushover push failed", error=str(e))
                return False
        self.logger.info("No Telegram or Pushover configured; set TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID or PUSHOVER_*")
        return False

    def alert(self, opportunity: Opportunity) -> None:
        msg = self.craft_message(opportunity)
        self.push(msg, deal_url=opportunity.deal.url or None)
        self.logger.info("Alert sent for opportunity", url=opportunity.deal.url)


class PlanningAgent:
    """Orchestrates Scanner -> Ensemble -> Messaging"""

    def __init__(self, collection=None, memory: Optional[DealMemory] = None, deal_threshold: float = 3.0):
        self.logger = AgentLogger("Planning")
        self.memory = memory or DealMemory()
        self.deal_threshold = deal_threshold
        self.scanner = ScannerAgent()
        self.ensemble = EnsembleAgent(collection)
        self.messaging = MessagingAgent()

    def run_one(self, deal: Deal) -> Opportunity:
        estimate = self.ensemble.price(deal.product_description)
        discount = estimate - deal.price
        return Opportunity(deal=deal, estimate=estimate, discount=discount)

    def plan(self) -> Optional[Opportunity]:
        init_logging()
        selection = self.scanner.scan(self.memory)
        if not selection or not selection.deals:
            self.logger.info("No new deals from scanner")
            return None
        opportunities = [self.run_one(d) for d in selection.deals]
        opportunities.sort(key=lambda o: o.discount, reverse=True)
        best = opportunities[0]
        self.memory.mark_seen_batch([d.url for d in selection.deals])
        self.logger.info("Best opportunity", discount=best.discount, url=best.deal.url)
        self.messaging.alert(best)
        return best if best.discount >= self.deal_threshold else None
