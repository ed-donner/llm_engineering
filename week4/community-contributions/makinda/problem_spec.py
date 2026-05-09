"""
Problem specification and prompt builder for the VRP code-generation benchmark.

Defines the contract: generated code must write vrp_result.json with
total_cost, routes, and optional violations list.
"""

import json
from typing import Any


SYSTEM_PROMPT = """You are an expert in vehicle routing and optimization. You write correct, runnable Python 3 code only. No markdown code fences in your final code block—output only raw Python.

Problem: Multi-depot vehicle routing with time windows and traffic.

Constraints:
1. Each vehicle starts and ends at its assigned depot (start_depot_id).
2. Each order is served exactly once. Arrival before time window → wait until window_start. Arrival after window_end → late_penalty_per_min per minute late.
3. Vehicle capacity: total weight of orders on a route must not exceed capacity_kg.
4. Travel time = (distance_km / 30) * traffic_multiplier. Use traffic_multiplier = 1.4 for hours 7–9 and 16–19, else 1.0. Assume 30 km/h average speed.
5. Driver cost: wage_per_hour for first 8 hours, then overtime_per_hour_after_8h. Total cost = distance * fuel_cost_per_km + driver_time_cost + sum(late_penalty for late deliveries).

Input: A variable `dataset` is already in scope—a dict with keys "depots", "orders", "vehicles". Depots have id, lat, lon. Orders have order_id, lat, lon, weight_kg, window_start, window_end, late_penalty_per_min (window times in hours from midnight). Vehicles have vehicle_id, capacity_kg, start_depot_id, fuel_cost_per_km, wage_per_hour, overtime_per_hour_after_8h.

Output: Your code MUST write a JSON file named "vrp_result.json" with this exact structure:
{
  "total_cost": <float>,
  "routes": [ [order_id, order_id, ...], ... ],  // one list per vehicle, order of delivery
  "violations": [ "<description>", ... ]  // optional; list of constraint violations if any
}

If the problem is infeasible, still write vrp_result.json with total_cost = null or a large number, routes = [], and violations explaining why.

Write only Python code. No explanations before or after."""


def build_user_prompt(dataset: dict) -> str:
    """Build user message containing the dataset so the model can use it."""
    dataset_str = json.dumps(dataset, indent=2)
    return f"""Solve the following vehicle routing instance. The dataset is provided below. Your code will be executed with `dataset` already defined.

Dataset:
{dataset_str}

Remember: write your solution to "vrp_result.json" with keys total_cost, routes, violations."""
