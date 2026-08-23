import threading
import time
import logging
from datetime import datetime
from typing import Callable

from agents.fetcher import Fetcher
from agents.scorer import Scorer
from agents.summariser import Summariser
from agents.notifier import Notifier
from core.cache import SeenJobsCache

logger = logging.getLogger(__name__)


class Orchestrator:
    """Runs the job-fit pipeline in a background thread using injected agents and cache."""

    def __init__(
        self,
        cache: SeenJobsCache | None = None,
        fetcher: Fetcher | None = None,
        scorer: Scorer | None = None,
        summariser: Summariser | None = None,
        notifier: Notifier | None = None,
    ):
        self._cache = cache or SeenJobsCache()
        self._fetcher = fetcher or Fetcher()
        self._scorer = scorer or Scorer()
        self._summariser = summariser or Summariser()
        self._notifier = notifier or Notifier()

        self.state = {
            "running": False,
            "status": "Idle",
            "last_check": None,
            "jobs_scanned": 0,
            "alerts_sent": 0,
            "matches": [],
            "all_jobs": [],
            "logs": [],
        }
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def _log(self, msg: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}"
        self.state["logs"].insert(0, line)
        self.state["logs"] = self.state["logs"][:100]
        logger.info(msg)

    def _run_pipeline(
        self,
        cv_text: str,
        preferences: str,
        threshold: float,
        rss_feeds: list[str],
        seeker_name: str,
        on_update: Callable | None = None,
    ) -> None:
        """Single pipeline run — one full fetch → score → notify cycle."""
        self._log(f"🔍 Checking {len(rss_feeds)} RSS feeds...")

        try:
            jobs = self._fetcher.fetch_jobs(rss_feeds)
        except Exception as e:
            self._log(f"❌ Fetcher error: {e}")
            return

        new_jobs = [j for j in jobs if not self._cache.is_seen(j["id"])]
        self._log(f"📋 Found {len(jobs)} jobs | {len(new_jobs)} new")

        for job in new_jobs:
            self._cache.mark_seen(job["id"], job["title"], job["company"])
            self.state["jobs_scanned"] += 1

            try:
                score = self._scorer.score_fit(cv_text, job["description"])
                print(f"Score: {score}")
            except Exception as e:
                self._log(f"⚠️  Scorer error for '{job['title']}': {e}")
                score = 0.0

            job_row = {
                "title": job["title"],
                "company": job["company"],
                "score": round(score * 100, 1),
                "matched": score >= threshold,
                "url": job["url"],
                "time": datetime.now().strftime("%H:%M"),
            }
            self.state["all_jobs"].insert(0, job_row)
            self.state["all_jobs"] = self.state["all_jobs"][:200]

            if score >= threshold:
                self._log(f"✅ Match! '{job['title']}' @ {job['company']} — {score*100:.1f}%")

                try:
                    summary = self._summariser.summarise_match(cv_text, preferences, job)
                except Exception as e:
                    self._log(f"⚠️  Summariser error: {e}")
                    summary = f"Strong match at {score*100:.1f}% fit based on your profile."

                try:
                    match_data = {**job_row, "summary": summary}
                    self._notifier.send_notification(match_data, seeker_name)
                    self.state["alerts_sent"] += 1
                    self.state["matches"].insert(0, match_data)
                    self.state["matches"] = self.state["matches"][:50]
                    self._log(f"📲 Pushover notification sent for '{job['title']}'")
                except Exception as e:
                    self._log(f"❌ Notifier error: {e}")
            else:
                self._log(f"   Skip '{job['title']}' — {score*100:.1f}% (below {threshold*100:.0f}%)")

            if on_update:
                on_update()

        self.state["last_check"] = datetime.now().strftime("%H:%M:%S")

    def start(
        self,
        cv_text: str,
        preferences: str,
        threshold: float,
        rss_feeds: list[str],
        seeker_name: str,
        interval_minutes: int,
        on_update: Callable | None = None,
    ) -> None:
        if self.state["running"]:
            return

        self._stop_event.clear()
        self.state["running"] = True
        self.state["status"] = "Running"
        self._log(f"🚀 Agent started | interval={interval_minutes}m | threshold={threshold*100:.0f}%")

        def loop():
            while not self._stop_event.is_set():
                self.state["status"] = "Scanning..."
                self._run_pipeline(cv_text, preferences, threshold, rss_feeds, seeker_name, on_update)
                self.state["status"] = f"Waiting {interval_minutes}m for next check..."

                for _ in range(interval_minutes * 60):
                    if self._stop_event.is_set():
                        break
                    time.sleep(1)

            self.state["running"] = False
            self.state["status"] = "Stopped"
            self._log("⏹  Agent stopped")

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self.state["status"] = "Stopping..."
        self._log("⏹  Stop requested")

    def reset(self) -> None:
        """Clear all state for a fresh session."""
        self.stop()
        time.sleep(0.5)
        self.state.update({
            "running": False,
            "status": "Idle",
            "last_check": None,
            "jobs_scanned": 0,
            "alerts_sent": 0,
            "matches": [],
            "all_jobs": [],
            "logs": [],
        })
