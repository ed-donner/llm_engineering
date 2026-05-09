"""
PricingAgent — estimates the fair USD price of scraped products using
a fine-tuned Llama model running remotely on Modal.

Requires the pricer service to be deployed first:
    cd week8-project
    modal deploy pricer_service.py
"""

import logging
import sys
import os
from typing import Any, Dict, List

import modal

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# Deal verdict thresholds
# Verdict is based on the % savings relative to the model's estimated fair price.
# savings_pct = (estimated - scraped) / estimated * 100
# ---------------------------------------------------------------------------

GREAT_DEAL_SAVINGS = 20   # saving ≥ 20 % below estimate → Great Deal
GOOD_DEAL_SAVINGS  = 5    # saving ≥ 5 %  below estimate → Good Deal
FAIR_DEAL_MAX_OVER = 5    # up to 5 % above estimate      → Fair Price
# above that                                               → Overpriced


class PricingAgent:
    """
    An agent that enriches a list of scraped products with fair-value price
    estimates from a fine-tuned Llama model deployed on Modal.

    For each product it:
      1. Calls the remote Modal Pricer with the product title + description.
      2. Computes percentage savings vs the model's estimate.
      3. Appends four new fields to each product dict:
            - "estimated_price"  : float, model's fair-value estimate in USD
            - "discount"         : float, dollar amount saved vs the estimate
            - "savings_pct"      : float, percentage saved (negative = overpaying)
            - "verdict"          : str,   deal quality label

    Verdict formula (savings_pct = (estimated - scraped) / estimated × 100):
        ≥ 20 %  saved  →  Great Deal
        ≥  5 %  saved  →  Good Deal
        ≥ -5 %  (within ±5 %)  →  Fair Price
        <  -5 % (paying > 5 % over estimate)  →  Overpriced

    Usage:
        agent = PricingAgent()
        enriched = agent.enrich(products)   # products = list from ScraperAgent
    """

    name = "Pricing Agent"
    color = "\033[33m"   # yellow
    BG_BLACK = "\033[40m"
    RESET = "\033[0m"

    MODAL_APP_NAME = "week8-project-pricer"
    MODAL_CLASS_NAME = "Pricer"

    def __init__(self):
        """
        Connect to the remote Modal Pricer class on initialisation.

        Raises:
            RuntimeError: If the Modal service is not deployed or unreachable.
        """
        self.logger = logging.getLogger(self.name)
        self.log("PricingAgent initialising — connecting to Modal")

        try:
            Pricer = modal.Cls.from_name(self.MODAL_APP_NAME, self.MODAL_CLASS_NAME)
            self.pricer = Pricer()
            self.log("PricingAgent connected to Modal successfully")
        except Exception as exc:
            raise RuntimeError(
                f"Could not connect to Modal service '{self.MODAL_APP_NAME}'. "
                f"Make sure you have run: modal deploy pricer_service.py\n"
                f"Original error: {exc}"
            ) from exc

    def log(self, message: str) -> None:
        """
        Log an info message prefixed with the agent name and coloured output.

        Args:
            message: The message to log.
        """
        styled = f"{self.BG_BLACK}{self.color}[{self.name}] {message}{self.RESET}"
        self.logger.info(styled)

    def _estimate_price(self, product: Dict[str, Any]) -> float:
        """
        Call the remote Llama model to estimate the fair price of one product.

        Builds a concise description from the product title + description and
        sends it to the Modal-hosted fine-tuned model.

        Args:
            product: A product dict as returned by ScraperAgent.

        Returns:
            Estimated fair price in USD as a float.
        """
        description = f"{product['title']}. {product['description']}."
        self.log(f"Estimating price for: {product['title'][:60]}...")
        estimate = self.pricer.price.remote(description)
        self.log(f"Estimate received: ${estimate:.2f}")
        return estimate

    def _verdict(self, scraped_price: float, estimated_price: float) -> tuple:
        """
        Compute deal verdict and percentage savings.

        Uses percentage savings relative to the estimated fair price so the
        threshold is scale-independent (works equally well for a $10 item
        and a $1,000 item).

        Args:
            scraped_price: The price found on Jumia (USD).
            estimated_price: The model's fair-value estimate (USD).

        Returns:
            Tuple of (verdict_str, savings_pct_float).
            verdict_str is one of: "Great Deal", "Good Deal", "Fair Price", "Overpriced".
            savings_pct is positive when the item is cheaper than the estimate.
        """
        if estimated_price <= 0:
            return "Unknown", 0.0

        savings_pct = (estimated_price - scraped_price) / estimated_price * 100

        if savings_pct >= GREAT_DEAL_SAVINGS:
            verdict = "Great Deal"
        elif savings_pct >= GOOD_DEAL_SAVINGS:
            verdict = "Good Deal"
        elif savings_pct >= -FAIR_DEAL_MAX_OVER:
            verdict = "Fair Price"
        else:
            verdict = "Overpriced"

        return verdict, round(savings_pct, 1)

    def enrich(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich a list of scraped products with price estimates and deal verdicts.

        Calls the remote Llama model once per product and adds four fields
        to each dict: estimated_price, discount, savings_pct, and verdict.

        Args:
            products: List of product dicts from ScraperAgent.scrape().

        Returns:
            The same list with extra fields added to each item:
                - "estimated_price" (float) : model's fair-value estimate in USD
                - "discount"        (float) : dollar savings (estimated - scraped)
                - "savings_pct"     (float) : percentage saved vs estimate
                - "verdict"         (str)   : deal quality label
        """
        self.log(f"Enriching {len(products)} products with price estimates")
        enriched = []

        for product in products:
            try:
                scraped_price = float(product.get("price", 0))
                estimated = self._estimate_price(product)
                discount = round(estimated - scraped_price, 2)
                verdict, savings_pct = self._verdict(scraped_price, estimated)

                enriched.append({
                    **product,
                    "estimated_price": round(estimated, 2),
                    "discount": discount,
                    "savings_pct": savings_pct,
                    "verdict": verdict,
                })

            except Exception as exc:
                self.log(f"Warning: could not price '{product.get('title', '?')}': {exc}")
                enriched.append({
                    **product,
                    "estimated_price": 0.0,
                    "discount": 0.0,
                    "savings_pct": 0.0,
                    "verdict": "Unknown",
                })

        self.log("Enrichment complete")
        return enriched
