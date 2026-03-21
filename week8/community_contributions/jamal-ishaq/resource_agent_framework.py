import json
import logging
import os
import sys
from typing import List
from dotenv import load_dotenv

from agents.autonomous_planning_agent import AutonomousPlanningAgent
from agents.resources import ResourceOpportunity

load_dotenv(override=True)

BG_BLUE = "\033[44m"
WHITE = "\033[37m"
RESET = "\033[0m"


def init_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] [ResourceScout] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)


class ResourceScoutFramework:
    MEMORY_FILENAME = "memory.json"

    def __init__(self):
        init_logging()
        self.memory: List[ResourceOpportunity] = self.read_memory()
        self.autonomous_planner = None

    def log(self, message: str) -> None:
        payload = BG_BLUE + WHITE + "[Agent Framework] " + message + RESET
        logging.info(payload)

    def _memory_path(self) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, self.MEMORY_FILENAME)

    def read_memory(self) -> List[ResourceOpportunity]:
        path = self._memory_path()
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as file:
            raw = json.load(file)
        return [ResourceOpportunity(**item) for item in raw]

    def write_memory(self) -> None:
        path = self._memory_path()
        serializable = [item.model_dump() for item in self.memory]
        with open(path, "w", encoding="utf-8") as file:
            json.dump(serializable, file, indent=2)

    def init_agents_as_needed(self) -> None:
        if not self.autonomous_planner:
            self.log("Initializing autonomous planner")
            self.autonomous_planner = AutonomousPlanningAgent()

    def run(self, topic: str = "llm agents") -> List[ResourceOpportunity]:
        self.init_agents_as_needed()
        self.log("Running autonomous top-5 cycle")
        latest_results = self.autonomous_planner.plan(topic=topic, memory=self.memory)
        self._merge_memory(latest_results)
        return latest_results

    def autorun(self, topic: str = "llm agents") -> List[ResourceOpportunity]:
        return self.run(topic=topic)

    def _merge_memory(self, latest_results: List[ResourceOpportunity]) -> None:
        known = {item.resource.url for item in self.memory}
        new_items = [
            item for item in latest_results if item.resource.url not in known
        ]
        if new_items:
            self.memory.extend(new_items)
            self.write_memory()
