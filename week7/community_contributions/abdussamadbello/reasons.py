"""
Reasons: one-sentence explanation for "Why might this product cost around $X?"
Supports same-model (second prompt) or API (LiteLLM/OpenAI/Anthropic).
"""
from __future__ import annotations

from typing import Optional


def get_reason_same_model(
    summary: str,
    pred_price: float,
    pred_category: Optional[str],
    generate_fn,
) -> str:
    """
    Use the same (fine-tuned) model with a second prompt to get a one-sentence reason.
    generate_fn: callable(prompt: str) -> str (model completion).
    """
    cat_part = f" and category {pred_category}" if pred_category else ""
    prompt = (
        f"You predicted this product costs ${pred_price:.0f}{cat_part}. "
        f"In one sentence, why might it cost around ${pred_price:.0f}?\n\nProduct: {summary[:400]}\n\nReason:"
    )
    return (generate_fn(prompt) or "").strip()[:300]


def get_reason_api(
    summary: str,
    pred_price: float,
    pred_category: Optional[str],
    model: str = "gpt-4o-mini",
) -> str:
    """
    Call an API model (e.g. GPT-4o-mini, Claude) for the reason. Requires OPENAI_API_KEY or ANTHROPIC_API_KEY.
    """
    try:
        import os
        import litellm
        litellm.drop_params = True
        cat_part = f" and category {pred_category}" if pred_category else ""
        msg = (
            f"You predicted this product costs ${pred_price:.0f}{cat_part}. "
            f"In one sentence, why might it cost around ${pred_price:.0f}? "
            f"Product: {summary[:400]}"
        )
        r = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": msg}],
            max_tokens=80,
        )
        out = (r.choices[0].message.content or "").strip()[:300]
        return out
    except Exception as e:
        return f"(API reason failed: {e})"


def get_reason(
    summary: str,
    pred_price: float,
    pred_category: Optional[str] = None,
    *,
    generate_fn=None,
    use_api: bool = False,
    api_model: str = "gpt-4o-mini",
) -> str:
    """
    Return a one-sentence reason. Prefers generate_fn if provided; else use_api with api_model.
    """
    if generate_fn is not None:
        return get_reason_same_model(summary, pred_price, pred_category, generate_fn)
    if use_api:
        return get_reason_api(summary, pred_price, pred_category, model=api_model)
    return "(Set generate_fn or use_api=True to get reasons)"
