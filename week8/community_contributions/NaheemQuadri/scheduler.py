"""Runs the analysis pipeline every N minutes automatically.

Every interval:
  1. Fetch top 20 news articles from Finnhub
  2. For each article, run the full Claude agentic tool-calling loop
  3. Results are stored in a thread-safe queue read by the Gradio UI
  4. Pushover notifications are fired by Claude itself inside the loop

The scheduler runs in a background thread so Gradio stays responsive.
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from datetime import datetime
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler

from config import APP_CONFIG
from orchestrator import AnalysisResult, Orchestrator
from tools import fetch_news

logger = logging.getLogger(__name__)

#shared state (written by scheduler, read by Gradio)
_results_queue: deque[AnalysisResult] = deque(maxlen=200)
_queue_lock     = threading.Lock()
_last_run_at:   str  = "Never"
_is_running:    bool = False
_run_callbacks: list[Callable] = []   


def get_results() -> list[AnalysisResult]:
    """Return a snapshot of all completed results, newest first."""
    with _queue_lock:
        return list(reversed(_results_queue))


def get_status() -> dict[str, str | bool | int]:
    return {
        "last_run":     _last_run_at,
        "is_running":   _is_running,
        "total_results": len(_results_queue),
    }


def register_callback(fn: Callable) -> None:
    """Gradio registers a function here to trigger UI refresh after each run."""
    _run_callbacks.append(fn)


#core job

def _run_pipeline_job() -> None:
    global _last_run_at, _is_running

    if _is_running:
        logger.warning("Previous run still in progress — skipping this cycle.")
        return

    _is_running   = True
    _last_run_at  = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    logger.info("=== Scheduler: starting news analysis cycle ===")

    try:
        #fetch latest news
        news_data = fetch_news(
            categories=APP_CONFIG.news.news_categories,
            limit=APP_CONFIG.news.news_limit,
        )
        articles = news_data.get("articles", [])
        logger.info("Fetched %d articles.", len(articles))

        if not articles:
            logger.warning("No articles returned from Finnhub.")
            return

        orchestrator = Orchestrator()

        #analyse each article through Claude's agentic loop
        for i, article in enumerate(articles):
            logger.info("Analysing article %d/%d: %s",
                        i + 1, len(articles), article.get("headline", "")[:60])
            try:
                result = orchestrator.analyse(article)
                with _queue_lock:
                    _results_queue.append(result)
            except Exception as exc:          
                logger.exception("Failed on article %d: %s", i + 1, exc)

        logger.info("=== Cycle complete. %d results stored. ===", len(_results_queue))

    except Exception as exc:                 
        logger.exception("Scheduler job failed: %s", exc)

    finally:
        _is_running = False
        
        for cb in _run_callbacks:
            try:
                cb()
            except Exception:                 
                pass


#scheduler

class NewsScheduler:
    """
    Wraps APScheduler. Call start() once when the app boots.
    The first run fires immediately; subsequent runs every N minutes.
    """

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler(timezone="UTC")
        self._interval  = APP_CONFIG.news.interval_minutes

    def start(self) -> None:
        if self._scheduler.running:
            return
        #fire immediately on start, then repeat every interval
        self._scheduler.add_job(
            _run_pipeline_job,
            trigger="interval",
            minutes=self._interval,
            id="news_analysis",
            next_run_time=datetime.utcnow(), 
            max_instances=1,
        )
        self._scheduler.start()
        logger.info(
            "NewsScheduler started — running every %d minutes.", self._interval
        )

    def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("NewsScheduler stopped.")

    def run_now(self) -> None:
        """Trigger an immediate out-of-cycle run (called from Gradio button)."""
        threading.Thread(target=_run_pipeline_job, daemon=True).start()

    @property
    def is_running(self) -> bool:
        return _is_running
