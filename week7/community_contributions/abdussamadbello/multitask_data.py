"""
Multi-task prompt/completion format: Category + Price in one completion.
Format: "Category: X. Price is $Y.00"
"""
import re
from typing import Optional

# Prompt/completion format used for multi-task (category + price)
MULTITASK_QUESTION = (
    "What category is this product and what does it cost to the nearest dollar? "
    "Reply with: Category: <category>. Price is $<number>."
)
MULTITASK_PREFIX = "Category: "


def build_multitask_prompt(summary: str, prefix: str = MULTITASK_PREFIX) -> str:
    """Build the multi-task prompt (no completion)."""
    return f"{MULTITASK_QUESTION}\n\n{summary}\n\n{prefix}"


def build_multitask_completion(category: str, price: float, do_round: bool = True) -> str:
    """Build the multi-task completion string."""
    p = round(price) if do_round else price
    return f"{category}. Price is ${p}.00"


def parse_multitask_completion(completion: str) -> tuple[Optional[str], float]:
    """
    Parse model output into (category, price).
    Returns (None, 0.0) if parsing fails.
    """
    completion = (completion or "").strip()
    # Try "Category: X. Price is $Y" or "X. Price is $Y"
    price_match = re.search(r"Price is\s*\$?\s*([-+]?\d*\.?\d+)", completion, re.I)
    price = float(price_match.group(1)) if price_match else 0.0

    # Category: first part before "Price is" or before ". Price"
    category = None
    if "Price is" in completion:
        left = completion.split("Price is")[0].strip()
        # Remove "Category:" if present
        if left.lower().startswith("category:"):
            left = left[9:].strip()
        if left.endswith("."):
            left = left[:-1].strip()
        if left:
            category = left

    return (category, price)


def item_to_multitask_datapoint(item, tokenizer, max_tokens: int, do_round: bool = True) -> dict:
    """
    Turn an Item into prompt/completion for multi-task.
    Truncates summary to max_tokens. item must have .summary, .category, .price.
    """
    summary = getattr(item, "summary", None) or ""
    tokens = tokenizer.encode(summary, add_special_tokens=False)
    if len(tokens) > max_tokens:
        summary = tokenizer.decode(tokens[:max_tokens]).rstrip()

    prompt = build_multitask_prompt(summary)
    completion = build_multitask_completion(item.category, item.price, do_round=do_round)
    return {"prompt": prompt, "completion": completion}
