"""
Indie Publisher / Funding Matcher – Agent framework.

Orchestrates: Scanner (curated opportunities) -> RAG + LLM fit scoring -> Planning -> Messaging.
Uses Week 5 game_publisher_db for RAG when available.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from agents.planning_agent import PlanningAgent
from publisher_models import ScoredOpportunity

load_dotenv(override=True)

BG_BLUE = "\033[44m"
WHITE = "\033[37m"
RESET = "\033[0m"


def init_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] [Publisher Matcher] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)


class PublisherMatcherFramework:
    """Framework that runs the publisher/funding opportunity matcher."""

    MEMORY_FILENAME = "publisher_matcher_memory.json"
    MEMORY_PATH = Path(__file__).resolve().parent / MEMORY_FILENAME

    def __init__(self) -> None:
        init_logging()
        self.memory: List[ScoredOpportunity] = self._read_memory()
        self.planner: PlanningAgent | None = None

    def _read_memory(self) -> List[ScoredOpportunity]:
        if not self.MEMORY_PATH.exists():
            return []
        try:
            with open(self.MEMORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [ScoredOpportunity(**item) for item in data]
        except Exception:
            return []

    def _write_memory(self) -> None:
        data = [s.model_dump() for s in self.memory]
        with open(self.MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def init_agents_as_needed(self) -> None:
        if self.planner is None:
            logging.info(f"{BG_BLUE}{WHITE}[Publisher Matcher] Initializing agents{RESET}")
            self.planner = PlanningAgent()
            logging.info(f"{BG_BLUE}{WHITE}[Publisher Matcher] Ready{RESET}")

    def run(self) -> tuple[List[ScoredOpportunity], str]:
        """
        Run one cycle: scan, score, optionally alert and add best to memory.
        Returns (memory, status_message) so the UI can show what happened.
        """
        self.init_agents_as_needed()
        result = self.planner.plan(memory=self.memory)
        if result is not None:
            self.memory.append(result)
            self._write_memory()
            msg = f"Added: **{result.opportunity.name}** (Fit {result.fit_score:.0f})."
            return self.memory, msg
        # result is None only when scanner found no new opportunities (all URLs already in memory)
        msg = (
            "No new opportunities — everything from the list is already in the table. "
            "Use **Reset memory** below to clear and re-score from scratch, or add more in `opportunities_data.json`."
        )
        return self.memory, msg

    @classmethod
    def reset_memory(cls) -> None:
        """Clear saved opportunities (for testing)."""
        if cls.MEMORY_PATH.exists():
            cls.MEMORY_PATH.unlink()
            logging.info("Publisher matcher memory reset.")


if __name__ == "__main__":
    framework = PublisherMatcherFramework()
    framework.init_agents_as_needed()
    framework.run()
