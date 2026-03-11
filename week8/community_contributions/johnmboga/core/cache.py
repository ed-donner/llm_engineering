"""
core/cache.py
Persistent deduplication cache for seen job listings.
Uses a simple JSON file so state survives restarts.
"""

import json
import os
from datetime import datetime
from threading import Lock


class SeenJobsCache:
    """Thread-safe cache of seen job IDs with optional file persistence."""

    def __init__(self, cache_file: str = "seen_jobs.json"):
        self._cache_file = cache_file
        self._lock = Lock()

    def _load(self) -> dict:
        if not os.path.exists(self._cache_file):
            return {}
        try:
            with open(self._cache_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: dict) -> None:
        with open(self._cache_file, "w") as f:
            json.dump(data, f, indent=2)

    def is_seen(self, job_id: str) -> bool:
        """Return True if this job has already been processed."""
        with self._lock:
            cache = self._load()
            return job_id in cache

    def mark_seen(self, job_id: str, title: str, company: str) -> None:
        """Record a job as processed."""
        with self._lock:
            cache = self._load()
            cache[job_id] = {
                "title": title,
                "company": company,
                "seen_at": datetime.now().isoformat(),
            }
            self._save(cache)

    def count(self) -> int:
        with self._lock:
            return len(self._load())

    def clear(self) -> None:
        """Reset the cache — useful for testing."""
        with self._lock:
            self._save({})
