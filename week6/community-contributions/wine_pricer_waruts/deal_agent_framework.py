import os
import sys
import logging
import json
from typing import List
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from agents.deals import Opportunity
from sklearn.manifold import TSNE
import numpy as np

load_dotenv(override=True)

# Colors for logging
BG_BLUE = "\033[44m"
WHITE = "\033[37m"
RESET = "\033[0m"

# Colors for plot
CATEGORIES = ["US", "France", "Italy", "Spain", "Portugal", "Chile", "Argentina", "Austria", "Germany", "Australia", "Other"]
COLORS = ["blue", "red", "green", "orange", "purple", "cyan", "brown", "pink", "gold", "magenta", "gray"]

# Which planner the framework uses: "langgraph" (the LangGraph graph) or "fixed" (Ed's PlanningAgent)
PLANNER = "langgraph"


def init_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not any(getattr(handler, "agent_framework", False) for handler in root.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        handler.agent_framework = True
        formatter = logging.Formatter(
            "[%(asctime)s] [Agents] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S %z",
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)
    for noisy in ("httpx", "httpcore", "urllib3", "sentence_transformers", "LiteLLM", "litellm"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


class DealAgentFramework:
    DB = "wines_vectorstore"
    COLLECTION = "wines"
    MEMORY_FILENAME = "memory.json"

    def __init__(self):
        init_logging()
        # Qdrant's local mode allows one client per folder, so the whole app shares this one
        self.client = QdrantClient(path=self.DB)
        self.memory = self.read_memory()
        self.planner = None

    def init_agents_as_needed(self):
        if not self.planner:
            self.log(f"Initializing Agent Framework with the {PLANNER} planner")
            if PLANNER == "langgraph":
                from agents.langgraph_planning_agent import LangGraphPlanningAgent
                self.planner = LangGraphPlanningAgent(self.client)
            else:
                from agents.planning_agent import PlanningAgent
                self.planner = PlanningAgent(self.client)
            self.log("Agent Framework is ready")

    def read_memory(self) -> List[Opportunity]:
        if os.path.exists(self.MEMORY_FILENAME):
            with open(self.MEMORY_FILENAME, "r") as file:
                data = json.load(file)
            opportunities = [Opportunity(**item) for item in data]
            return opportunities
        return []

    def write_memory(self) -> None:
        data = [opportunity.model_dump() for opportunity in self.memory]
        with open(self.MEMORY_FILENAME, "w") as file:
            json.dump(data, file, indent=2)

    @classmethod
    def reset_memory(cls) -> None:
        """
        Forget every deal surfaced so far, so they can be found again
        """
        with open(cls.MEMORY_FILENAME, "w") as file:
            json.dump([], file)

    def log(self, message: str):
        text = BG_BLUE + WHITE + "[Agent Framework] " + message + RESET
        logging.info(text)

    def run(self) -> List[Opportunity]:
        self.init_agents_as_needed()
        logging.info("Kicking off Planning Agent")
        result = self.planner.plan(memory=self.memory)
        logging.info(f"Planning Agent has completed and returned: {result}")
        if result:
            self.memory.append(result)
            self.write_memory()
        return self.memory

    def get_plot_data(self, max_datapoints=800):
        points, _ = self.client.scroll(self.COLLECTION, limit=max_datapoints, with_vectors=True, with_payload=True)
        vectors = np.array([point.vector for point in points])
        documents = [point.payload["summary"] for point in points]
        colors = [COLORS[CATEGORIES.index(point.payload["category"])] for point in points]
        tsne = TSNE(n_components=3, random_state=42, n_jobs=-1)
        reduced_vectors = tsne.fit_transform(vectors)
        return documents, reduced_vectors, colors

    def close(self):
        self.client.close()


if __name__ == "__main__":
    DealAgentFramework().run()
