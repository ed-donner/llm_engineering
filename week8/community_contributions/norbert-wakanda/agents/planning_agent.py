"""
PlanningAgent — orchestrates ScraperAgent and PricingAgent into a single pipeline.

The PlanningAgent is the top-level coordinator:
  1. Receives a natural-language query from the user.
  2. Delegates scraping to ScraperAgent → structured product list.
  3. Delegates pricing to PricingAgent → enriched product list with verdicts.
  4. Returns the enriched list plus a human-readable summary.

This is the only class the Gradio UI needs to interact with.
"""

import logging
from typing import Any, Dict, List, Tuple

from agents.scraper_agent import ScraperAgent
from agents.pricing_agent import PricingAgent


VERDICT_EMOJI = {
    "Great Deal": "🔥",
    "Good Deal":  "✅",
    "Fair Price": "🟡",
    "Overpriced": "❌",
    "Unknown":    "❓",
}


class PlanningAgent:
    """
    High-level orchestrator that coordinates the full deal-finding pipeline.

    Responsibilities:
      - Validate and normalise the incoming user query.
      - Delegate scraping to ScraperAgent.
      - Delegate price estimation to PricingAgent.
      - Produce a structured result list and a plain-text summary.

    The two sub-agents are created once on __init__ and reused across calls
    so Modal's warm container is not discarded between runs.

    Usage:
        planner = PlanningAgent()
        products, summary = planner.run("I want budget laptops")
    """

    name = "Planning Agent"
    color = "\033[35m"   # magenta
    BG_BLACK = "\033[40m"
    RESET = "\033[0m"

    def __init__(self):
        """
        Initialise the PlanningAgent and all sub-agents.

        Raises:
            RuntimeError: If PricingAgent cannot connect to Modal.
        """
        self.logger = logging.getLogger(self.name)
        self.log("Initialising sub-agents…")
        self.scraper = ScraperAgent()
        self.pricer  = PricingAgent()
        self.log("All sub-agents ready.")

    def log(self, message: str) -> None:
        """
        Log an info message with agent name and colour prefix.

        Args:
            message: The message to log.
        """
        styled = f"{self.BG_BLACK}{self.color}[{self.name}] {message}{self.RESET}"
        self.logger.info(styled)

    def _validate_query(self, query: str) -> str:
        """
        Clean and validate the user's query.

        Args:
            query: Raw input string from the user.

        Returns:
            Stripped, non-empty query string.

        Raises:
            ValueError: If the query is empty after stripping.
        """
        query = query.strip()
        if not query:
            raise ValueError("Query must not be empty.")
        return query

    def _build_summary(self, products: List[Dict[str, Any]], query: str) -> str:
        """
        Build a human-readable plain-text summary of the enriched product list.

        Args:
            products: Enriched product dicts (output of PricingAgent.enrich).
            query: The original user query.

        Returns:
            Multi-line summary string suitable for display in the Gradio UI.
        """
        lines = [f'Results for: "{query}"', ""]

        for i, p in enumerate(products, 1):
            emoji   = VERDICT_EMOJI.get(p.get("verdict", "Unknown"), "❓")
            title   = p.get("title", "Unknown")
            price   = p.get("price", "?")
            est     = p.get("estimated_price", 0)
            savings = p.get("savings_pct", 0.0)
            verdict = p.get("verdict", "Unknown")

            savings_str = (
                f"+{savings:.1f}% over estimate"
                if savings < 0
                else f"{savings:.1f}% below estimate"
            )

            lines.append(
                f"{i}. {emoji} [{verdict}] {title}\n"
                f"   Jumia price: ${price}  |  Est. fair price: ${est:.2f}  |  {savings_str}"
            )

        return "\n".join(lines)

    def run(self, query: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        Run the full deal-finding pipeline for a user query.

        Steps:
          1. Validate the query.
          2. ScraperAgent scrapes Jumia and returns 5 structured products.
          3. PricingAgent enriches each product with estimated price + verdict.
          4. Build and return a plain-text summary.

        Args:
            query: Natural-language product request,
                   e.g. "I want budget laptops under $300".

        Returns:
            Tuple of:
              - enriched_products: list of dicts with all product + pricing fields.
              - summary: human-readable plain-text deal summary.

        Raises:
            ValueError: If the query is empty or the scraper returns bad data.
            RuntimeError: If Modal is unreachable.
        """
        query = self._validate_query(query)
        self.log(f"Pipeline starting for query: '{query}'")

        self.log("Step 1/2 — scraping products…")
        products = self.scraper.scrape(query)
        self.log(f"Scraped {len(products)} products.")

        self.log("Step 2/2 — estimating prices…")
        enriched = self.pricer.enrich(products)
        self.log("Pipeline complete.")

        summary = self._build_summary(enriched, query)
        return enriched, summary
