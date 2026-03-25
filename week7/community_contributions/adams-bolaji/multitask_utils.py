"""
Multi-task Pricer Utilities – Project 5: Price + Category Prediction
Author: adams-bolaji

Helpers for multi-task SFT format: predict both product category and price.
"""

import re
from typing import Optional


# === Multi-task format ===
MULTITASK_QUESTION = (
    "What category is this product and what does it cost to the nearest dollar? "
    "Reply with: Category: <category>. Price is $<number>."
)
MULTITASK_PREFIX = "Category: "


def build_multitask_prompt(summary: str) -> str:
    """Build prompt for multi-task (category + price) prediction."""
    return f"{MULTITASK_QUESTION}\n\n{summary}\n\n{MULTITASK_PREFIX}"


def build_multitask_completion(category: str, price: float, do_round: bool = True) -> str:
    """Build completion string: Category: X. Price is $Y.00"""
    p = round(price) if do_round else price
    return f"{category}. Price is ${p}.00"


def parse_multitask_completion(completion: str) -> tuple[Optional[str], float]:
    """
    Parse model output into (category, price).
    Returns (None, 0.0) for price if not found.
    """
    completion = (completion or "").strip()
    price_match = re.search(r"Price is\s*\$?\s*([-+]?\d*\.?\d+)", completion, re.I)
    price = float(price_match.group(1)) if price_match else 0.0

    category = None
    if "Price is" in completion:
        left = completion.split("Price is")[0].strip()
        if left.lower().startswith("category:"):
            left = left[9:].strip()
        if left.endswith("."):
            left = left[:-1].strip()
        if left:
            category = left

    return (category, price)


def normalize_category_for_match(cat: Optional[str]) -> str:
    """Normalize category for comparison (lowercase, replace underscores with spaces)."""
    if not cat:
        return ""
    return cat.lower().replace("_", " ").strip()


def category_matches(pred: Optional[str], truth: str) -> bool:
    """Check if predicted category matches ground truth (normalized)."""
    if not pred:
        return False
    return normalize_category_for_match(pred) == normalize_category_for_match(truth)


def extract_price_from_output(value) -> float:
    """Extract numeric price from string (e.g. '$1,234.56' or '1234')."""
    if isinstance(value, (int, float)):
        return float(value)
    value = str(value).replace("$", "").replace(",", "")
    match = re.search(r"[-+]?\d*\.?\d+", value)
    return float(match.group()) if match else 0.0
