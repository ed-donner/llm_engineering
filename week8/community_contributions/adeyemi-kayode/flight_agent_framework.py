"""
Autonomous multi-agent framework for Africa flight prices.
Orchestrates: RouteScanner → FlightPricer → Planning → Messaging.
Reference: week8 deal_agent_framework.py; domain: week6 adeyemi-kayode (Africa flight data).
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from agents.flight_deals import FlightOpportunity, FlightRoute
from agents.planning_agent import FlightPlanningAgent
from agents.route_scanner_agent import RouteScannerAgent

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
            "[%(asctime)s] [Agents] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)


class FlightAgentFramework:
    """
    Runs the autonomous multi-agent pipeline: scan routes → price → rank → notify.
    Memory stores seen route keys (optional) to avoid re-notifying.
    """

    MEMORY_FILENAME = "flight_memory.json"
    DATA_DIR = Path(__file__).parent / "data"

    def __init__(self, routes_file: Optional[Path] = None, use_llm_scanner: bool = False):
        init_logging()
        self.memory = self._read_memory()
        routes_path = routes_file or self.DATA_DIR / "routes.json"
        self._ensure_routes_file(routes_path)
        self.scanner = RouteScannerAgent(routes_file=routes_path, use_llm=use_llm_scanner)
        self.planner: Optional[FlightPlanningAgent] = None
        self._log("FlightAgentFramework initialized")

    def _log(self, message: str) -> None:
        logging.info(BG_BLUE + WHITE + "[Flight Agent Framework] " + message + RESET)

    def _read_memory(self) -> List[str]:
        path = Path(__file__).parent / self.MEMORY_FILENAME
        if path.exists():
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _write_memory(self) -> None:
        path = Path(__file__).parent / self.MEMORY_FILENAME
        with open(path, "w") as f:
            json.dump(self.memory, f, indent=2)

    def _ensure_routes_file(self, path: Path) -> None:
        """If routes.json doesn't exist, create a small default from common Africa routes."""
        if path.exists():
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        default_routes = [
            {"origin_city": "Lagos", "origin_country": "Nigeria", "destination_city": "Nairobi", "destination_country": "Kenya"},
            {"origin_city": "Lagos", "origin_country": "Nigeria", "destination_city": "Accra", "destination_country": "Ghana"},
            {"origin_city": "Nairobi", "origin_country": "Kenya", "destination_city": "Johannesburg", "destination_country": "South Africa"},
            {"origin_city": "Cairo", "origin_country": "Egypt", "destination_city": "Lagos", "destination_country": "Nigeria"},
        ]
        with open(path, "w") as f:
            json.dump(default_routes, f, indent=2)
        self._log(f"Created default routes file: {path}")

    def init_agents_as_needed(self) -> None:
        if self.planner is None:
            self._log("Initializing agents (Scanner, Pricer, Planning, Messaging)")
            self.planner = FlightPlanningAgent()
            self.planner.scanner = self.scanner
            self._log("Agents ready")

    def run(self, user_query: Optional[str] = None) -> List[FlightOpportunity]:
        """
        One autonomous run: scan routes (from file or user_query) → price → rank → notify best.
        Returns list of opportunities (best first).
        """
        self.init_agents_as_needed()
        self._log("Starting Planning Agent run")
        best = self.planner.plan(memory_seen=self.memory, user_query=user_query, notify_best=True)
        if best:
            key = best.quote.route.describe()
            if key not in self.memory:
                self.memory.append(key)
                self._write_memory()
            self._log(f"Best opportunity: {best.quote.route.describe()} @ ${best.quote.price_usd:.2f}")
            return [best]
        return []


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Africa flight price autonomous agents")
    parser.add_argument("--query", type=str, help="Natural language route query (requires OPENAI_API_KEY)")
    parser.add_argument("--llm-scanner", action="store_true", help="Use LLM to parse --query")
    args = parser.parse_args()
    framework = FlightAgentFramework(use_llm_scanner=bool(args.llm_scanner))
    opportunities = framework.run(user_query=args.query)
    if opportunities:
        print("\nBest deal:", framework.planner.messenger.format_opportunity(opportunities[0]))
    else:
        print("\nNo routes or quotes this run. Add data/routes.json or use --query with --llm-scanner.")
