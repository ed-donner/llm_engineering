"""
Scoring for VRP benchmark.

Score = 50% (Cost Normalized) + 20% (Feasibility) + 15% (Runtime) + 10% (Code Stability) + 5% (Token Efficiency)
Feasibility: hard constraint violation → heavy penalty.
"""

from typing import Any


# Weights (must sum to 1.0)
W_COST = 0.50
W_FEASIBILITY = 0.20
W_RUNTIME = 0.15
W_STABILITY = 0.10
W_TOKENS = 0.05


def normalize_cost(cost: float | None, reference_cost: float | None) -> float:
    """
    Lower cost is better. Score 0–1: 1 = best (low cost).
    If reference_cost given, score = reference_cost / max(cost, reference_cost).
    Else use a fixed high baseline (e.g. 1e6) so lower cost → higher score.
    """
    if cost is None or cost < 0:
        return 0.0
    baseline = reference_cost if reference_cost and reference_cost > 0 else 100_000.0
    # Score: 1 when cost = 0, decays as cost increases. Use 1 / (1 + cost/baseline) so 0 cost → 1
    return 1.0 / (1.0 + cost / baseline)


def normalize_runtime(runtime_seconds: float, timeout_seconds: float = 60) -> float:
    """Faster is better. 1 = instant, 0 = timeout."""
    if runtime_seconds <= 0:
        return 1.0
    return max(0, 1.0 - runtime_seconds / timeout_seconds)


def compute_score(
    execution: dict[str, Any],
    *,
    reference_cost: float | None = None,
    timeout_seconds: int = 60,
    input_tokens: int = 0,
    output_tokens: int = 0,
    token_baseline: int = 5000,
) -> tuple[float, dict[str, float]]:
    """
    execution: result from run_generated_code (success, total_cost, feasible, runtime_seconds, etc.)
    Returns (total_score 0–100, breakdown dict with component scores).
    """
    cost_score = normalize_cost(
        execution.get("total_cost"),
        reference_cost=reference_cost,
    )
    feasible = execution.get("feasible", False)
    feasibility_score = 1.0 if feasible else 0.0  # Hard: no partial credit
    runtime = execution.get("runtime_seconds") or 0
    runtime_score = normalize_runtime(runtime, timeout_seconds=timeout_seconds)
    stability_score = 1.0 if execution.get("success") else 0.0
    total_tokens = input_tokens + output_tokens
    token_score = 1.0 / (1.0 + total_tokens / token_baseline) if token_baseline else 1.0

    total = (
        W_COST * cost_score
        + W_FEASIBILITY * feasibility_score
        + W_RUNTIME * runtime_score
        + W_STABILITY * stability_score
        + W_TOKENS * token_score
    )
    total_pct = total * 100
    breakdown = {
        "cost": cost_score * 100,
        "feasibility": feasibility_score * 100,
        "runtime": runtime_score * 100,
        "stability": stability_score * 100,
        "tokens": token_score * 100,
    }
    return (total_pct, breakdown)
