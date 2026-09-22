"""
Real Estate Comps Agent Framework - Adams Bolaji
Orchestrates the full deal-finding pipeline with memory persistence.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv(override=True)

# Paths: adams-bolaji is inside week8/community_contributions/
ADAMS = Path(__file__).resolve().parent
WEEK8 = ADAMS.parent.parent  # week8/
if str(WEEK8) not in sys.path:
    sys.path.insert(0, str(WEEK8))
if str(ADAMS) not in sys.path:
    sys.path.insert(0, str(ADAMS))

import chromadb

from models import PropertyOpportunity

BG_BLUE = "\033[44m"
WHITE = "\033[37m"
RESET = "\033[0m"

DB_PATH = ADAMS / "real_estate_vectorstore"
COLLECTION_NAME = "sold_properties"
MEMORY_FILENAME = ADAMS / "memory.json"


def init_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] [RE Comps] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)


class RealEstateCompsFramework:
    """Main framework: loads comps DB, runs planning agent, persists opportunities."""

    def __init__(self):
        init_logging()
        self.memory = self.read_memory()
        client = chromadb.PersistentClient(path=str(DB_PATH))
        self.collection = client.get_or_create_collection(COLLECTION_NAME)
        self.planner = None

    def init_agents_as_needed(self):
        if not self.planner:
            self.log("Initializing Real Estate Comps Agent Framework")
            from re_comps.real_estate_planning_agent import RealEstatePlanningAgent
            self.planner = RealEstatePlanningAgent(self.collection)
            self.log("Agent Framework is ready")

    def read_memory(self) -> List[PropertyOpportunity]:
        if MEMORY_FILENAME.exists():
            with open(MEMORY_FILENAME) as f:
                data = json.load(f)
            return [PropertyOpportunity(**item) for item in data]
        return []

    def write_memory(self):
        data = [o.model_dump() for o in self.memory]
        with open(MEMORY_FILENAME, "w") as f:
            json.dump(data, f, indent=2)

    def log(self, msg: str):
        text = BG_BLUE + WHITE + "[RE Comps Framework] " + msg + RESET
        logging.info(text)

    def run(self) -> List[PropertyOpportunity]:
        self.init_agents_as_needed()
        self.log("Kicking off Real Estate Planning Agent")
        result = self.planner.plan(memory=self.memory)
        self.log(f"Planning Agent returned: {result}")
        if result:
            self.memory.append(result)
            self.write_memory()
        return self.memory


if __name__ == "__main__":
    RealEstateCompsFramework().run()
