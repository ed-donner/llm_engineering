import json
import logging
import os
from datetime import datetime
from typing import Any, List

LOG_FMT = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"


def init_logging(level=logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        h = logging.StreamHandler()
        h.setLevel(level)
        h.setFormatter(logging.Formatter(LOG_FMT, datefmt=DATE_FMT))
        root.addHandler(h)


class AgentLogger:
    """Per-agent logger for observability."""

    def __init__(self, agent_name: str):
        self._log = logging.getLogger(f"agent.{agent_name}")

    def info(self, msg: str, **kwargs: Any) -> None:
        extra = " " + str(kwargs) if kwargs else ""
        self._log.info(msg + extra)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log.error(msg + " " + str(kwargs) if kwargs else msg)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log.debug(msg + " " + str(kwargs) if kwargs else msg)


class DealMemory:
    """
    Memory so the planning agent does not surface the same deal twice.
    Persists seen deal URLs (and optional fingerprints).
    """

    def __init__(self, filepath: str = "deal_memory.json"):
        self.filepath = filepath
        self._seen_urls: set[str] = set()
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._seen_urls = set(data.get("urls", []))
            except Exception:
                self._seen_urls = set()

    def _save(self) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(
                {"urls": list(self._seen_urls), "updated": datetime.utcnow().isoformat() + "Z"},
                f,
                indent=2,
            )

    def seen(self, url: str) -> bool:
        self._load()
        return url in self._seen_urls

    def mark_seen(self, url: str) -> None:
        self._load()
        self._seen_urls.add(url)
        self._save()

    def mark_seen_batch(self, urls: List[str]) -> None:
        self._load()
        self._seen_urls.update(urls)
        self._save()

    def filter_new(self, urls: List[str]) -> List[str]:
        self._load()
        return [u for u in urls if u not in self._seen_urls]

    def clear(self) -> None:
        self._seen_urls.clear()
        self._save()
