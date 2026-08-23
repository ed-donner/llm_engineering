"""
Evaluation harness: execute generated Python code in a sandbox and capture metrics.

- Runs code with dataset in scope, timeout 60s.
- Reads vrp_result.json for total_cost, routes, violations.
- Validates routes against constraints and computes actual cost/violations.
"""

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from data_generator import haversine_km, get_traffic_multiplier


def validate_and_compute_cost(dataset: dict, result: dict) -> tuple[float, list[str]]:
    """
    Given dataset and model's result (routes, etc.), validate and compute actual cost.
    Returns (total_cost, list of violation messages).
    """
    depots = {d["id"]: d for d in dataset["depots"]}
    orders_by_id = {o["order_id"]: o for o in dataset["orders"]}
    vehicles = dataset["vehicles"]
    violations = []
    total_cost = 0.0

    served = set()
    for v in vehicles:
        vid = v["vehicle_id"]
        capacity = v["capacity_kg"]
        start_depot_id = v["start_depot_id"]
        fuel_cost = v["fuel_cost_per_km"]
        wage = v["wage_per_hour"]
        overtime = v["overtime_per_hour_after_8h"]
        depot = depots[start_depot_id]
        routes = result.get("routes") or []
        if vid >= len(routes):
            continue
        route = routes[vid]
        load = 0.0
        x, y = depot["lat"], depot["lon"]
        current_time = 6.0  # start of day
        drive_time = 0.0
        for oid in route:
            if oid in served:
                violations.append(f"Order {oid} served more than once")
            served.add(oid)
            if oid not in orders_by_id:
                violations.append(f"Unknown order id {oid}")
                continue
            o = orders_by_id[oid]
            load += o["weight_kg"]
            if load > capacity:
                violations.append(f"Vehicle {vid}: capacity exceeded (load={load}, cap={capacity})")
            dist = haversine_km(x, y, o["lat"], o["lon"])
            travel_h = (dist / 30.0) * get_traffic_multiplier(current_time)
            current_time += travel_h
            total_cost += dist * fuel_cost
            drive_time += travel_h
            # Arrival at order
            if current_time < o["window_start"]:
                current_time = o["window_start"]
            elif current_time > o["window_end"]:
                late_mins = (current_time - o["window_end"]) * 60
                total_cost += late_mins * o["late_penalty_per_min"]
                violations.append(f"Order {oid} late by {late_mins:.0f} min")
            # Service time 10 min
            current_time += 10 / 60.0
            x, y = o["lat"], o["lon"]
        # Return to depot
        dist = haversine_km(x, y, depot["lat"], depot["lon"])
        travel_h = (dist / 30.0) * get_traffic_multiplier(current_time)
        drive_time += travel_h
        total_cost += dist * fuel_cost
        total_cost += min(8, drive_time) * wage + max(0, drive_time - 8) * overtime

    for o in dataset["orders"]:
        if o["order_id"] not in served:
            violations.append(f"Order {o['order_id']} not served")
    return (total_cost, violations)


def extract_code(text: str) -> str:
    """Extract Python code from markdown code block if present."""
    text = text.strip()
    if "```python" in text:
        start = text.index("```python") + len("```python")
        end = text.find("```", start)
        if end == -1:
            return text[start:].strip()
        return text[start:end].strip()
    if "```" in text:
        start = text.index("```") + 3
        end = text.find("```", start)
        if end == -1:
            return text[start:].strip()
        return text[start:end].strip()
    return text


def run_generated_code(
    code: str,
    dataset: dict,
    timeout_seconds: int = 60,
    work_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Execute generated code with dataset in scope. Write dataset to a temp file,
    run code that loads it and writes vrp_result.json. Capture stdout, stderr, runtime.
    """
    code = extract_code(code)
    work_dir = work_dir or Path(tempfile.mkdtemp())
    dataset_path = work_dir / "dataset.json"
    result_path = work_dir / "vrp_result.json"
    with open(dataset_path, "w") as f:
        json.dump(dataset, f, indent=2)
    runner = '''import json
with open("dataset.json", "r") as f:
    dataset = json.load(f)
''' + code
    script_path = work_dir / "run_vrp.py"
    with open(script_path, "w") as f:
        f.write(runner)
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        runtime = time.perf_counter() - start
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        if proc.returncode != 0:
            return {
                "success": False,
                "runtime_seconds": runtime,
                "stdout": stdout,
                "stderr": stderr,
                "error": f"Exit code {proc.returncode}",
                "total_cost": None,
                "violations": [],
                "feasible": False,
            }
        if not result_path.exists():
            return {
                "success": False,
                "runtime_seconds": runtime,
                "stdout": stdout,
                "stderr": stderr,
                "error": "vrp_result.json not produced",
                "total_cost": None,
                "violations": [],
                "feasible": False,
            }
        with open(result_path) as f:
            result = json.load(f)
        total_cost = result.get("total_cost")
        violations = result.get("violations") or []
        # Validate and recompute cost if we have routes
        if result.get("routes") is not None:
            actual_cost, actual_violations = validate_and_compute_cost(dataset, result)
            violations = list(set(violations) | set(actual_violations))
            if total_cost is None or not violations:
                total_cost = actual_cost
        feasible = len(violations) == 0
        return {
            "success": True,
            "runtime_seconds": runtime,
            "stdout": stdout,
            "stderr": stderr,
            "total_cost": total_cost,
            "violations": violations,
            "feasible": feasible,
            "result": result,
        }
    except subprocess.TimeoutExpired:
        runtime = time.perf_counter() - start
        return {
            "success": False,
            "runtime_seconds": min(runtime, timeout_seconds),
            "stdout": "",
            "stderr": "",
            "error": f"Timeout after {timeout_seconds}s",
            "total_cost": None,
            "violations": [],
            "feasible": False,
        }
    except Exception as e:
        runtime = time.perf_counter() - start
        return {
            "success": False,
            "runtime_seconds": runtime,
            "stdout": "",
            "stderr": str(e),
            "error": str(e),
            "total_cost": None,
            "violations": [],
            "feasible": False,
        }
