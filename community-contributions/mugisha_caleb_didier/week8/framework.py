import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Set
from dotenv import load_dotenv, find_dotenv
import chromadb
from agents.planning_agent import PlanningAgent
from agents.models import Opportunity

load_dotenv(find_dotenv(), override=True)

ANSI_COLORS = {
    "\033[40m\033[36m": "#00dddd",  # Scanner (cyan)
    "\033[40m\033[34m": "#4488ff",  # Knowledge (blue)
    "\033[40m\033[33m": "#dddd00",  # Analysis (yellow)
    "\033[40m\033[32m": "#00dd00",  # Planning (green)
    "\033[40m\033[37m": "#87CEEB",  # Messenger (light blue)
    "\033[44m\033[37m": "#ff7800",  # Framework (orange)
}


def reformat(message):
    for ansi, color in ANSI_COLORS.items():
        message = message.replace(ansi, f'<span style="color:{color}">')
    message = message.replace("\033[0m", "</span>")
    return message


BG_BLUE = "\033[44m"
WHITE = "\033[37m"
RESET = "\033[0m"


def init_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if any(isinstance(h, logging.StreamHandler) and getattr(h, 'stream', None) == sys.stdout for h in root.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    root.addHandler(handler)


class NewsFramework:
    DB = "newshound_db"
    MEMORY_FILE = "newshound_memory.json"
    SEEN_URLS_FILE = "newshound_seen_urls.json"

    def __init__(self):
        init_logging()
        self.log("Initializing NewsHound Framework")
        client = chromadb.PersistentClient(path=self.DB)
        self.collection = client.get_or_create_collection("articles")
        self.memory = self._load_memory()
        self.seen_urls = self._load_seen_urls()
        self.planner = None
        self.alerts_sent = sum(1 for opp in self.memory if opp.alerted)
        self.last_scan: str = ""

    def init_agents(self):
        if not self.planner:
            self.log("Initializing agent pipeline")
            self.planner = PlanningAgent(self.collection)
            self.log("Agent pipeline ready")

    def _load_memory(self) -> List[Opportunity]:
        if os.path.exists(self.MEMORY_FILE):
            with open(self.MEMORY_FILE) as f:
                return [Opportunity(**item) for item in json.load(f)]
        return []

    def _save_memory(self):
        with open(self.MEMORY_FILE, "w") as f:
            json.dump([opp.model_dump() for opp in self.memory], f, indent=2)

    def _load_seen_urls(self) -> Set[str]:
        if os.path.exists(self.SEEN_URLS_FILE):
            with open(self.SEEN_URLS_FILE) as f:
                return set(json.load(f))
        return {opp.article.url for opp in self.memory}

    def _save_seen_urls(self):
        with open(self.SEEN_URLS_FILE, "w") as f:
            json.dump(list(self.seen_urls), f)

    def knowledge_size(self) -> int:
        return self.collection.count()

    def log(self, message):
        logging.info(BG_BLUE + WHITE + f"[Framework] {message}" + RESET)

    def run(self) -> List[Opportunity]:
        self.init_agents()
        self.log("Starting scan cycle")
        result = self.planner.plan(seen_urls=self.seen_urls)
        self.seen_urls.update(self.planner.processed_urls)
        self._save_seen_urls()
        if result:
            self.memory.append(result)
            self.alerts_sent += 1
            self._save_memory()
            self.log(f"New alert! {result.article.title[:60]}")
        else:
            self.log("No significant stories this cycle")
        self.last_scan = datetime.now().strftime("%H:%M:%S")
        self.log(f"Cycle complete. Total stories: {len(self.memory)}, Alerts: {self.alerts_sent}")
        return self.memory


if __name__ == "__main__":
    NewsFramework().run()
