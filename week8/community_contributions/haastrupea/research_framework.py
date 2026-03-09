"""
Investment Research Framework - main orchestrator.
Run from haastrupea directory: python research_framework.py
"""

import os
import sys
import logging
import json
from typing import List
from dotenv import load_dotenv
import chromadb

# Ensure haastrupea is on path when running as script
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

load_dotenv(override=True)

from agents.research_planning_agent import ResearchPlanningAgent
from models.research import ResearchOpportunity

BG_BLUE = "\033[44m"
WHITE = "\033[37m"
RESET = "\033[0m"


def init_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] [Research] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)


class ResearchFramework:
    DB = "research_vectorstore"
    MEMORY_FILENAME = "research_memory.json"

    def __init__(self):
        init_logging()
        db_path = os.path.join(_here, self.DB)
        mem_path = os.path.join(_here, self.MEMORY_FILENAME)
        self.db_path = db_path
        self.memory_path = mem_path
        client = chromadb.PersistentClient(path=db_path)
        self.memory = self.read_memory()
        self.collection = client.get_or_create_collection("filings")
        self.planner = None

    def init_agents_as_needed(self):
        if not self.planner:
            self.log("Initializing Research Framework")
            self.planner = ResearchPlanningAgent(self.collection)
            self.log("Research Framework is ready")

    def read_memory(self) -> List[ResearchOpportunity]:
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, "r") as f:
                    data = json.load(f)
                out = []
                for item in data:
                    # Ignore deprecated fields for backward compat
                    clean = {k: v for k, v in item.items() if k in ("ticker", "recommendation", "confidence", "summary", "url")}
                    if "summary" not in clean and "signals" in item:
                        sig = item.get("signals") or {}
                        clean["summary"] = sig.get("rag_summary", "")[:500]
                    out.append(ResearchOpportunity(**clean))
                return out
            except Exception:
                pass
        return []

    def write_memory(self) -> None:
        data = [opp.model_dump() for opp in self.memory]
        with open(self.memory_path, "w") as f:
            json.dump(data, f, indent=2)

    def log(self, message: str):
        text = BG_BLUE + WHITE + "[Research Framework] " + message + RESET
        logging.info(text)

    def run(self) -> List[ResearchOpportunity]:
        self.init_agents_as_needed()
        logging.info("Kicking off Research Planning Agent")
        urls_seen = [opp.url for opp in self.memory]
        result = self.planner.plan(memory=urls_seen)
        logging.info(f"Research Planning Agent completed: {result}")
        if result:
            self.memory.append(result)
            self.write_memory()
        return self.memory


if __name__ == "__main__":
    ResearchFramework().run()
