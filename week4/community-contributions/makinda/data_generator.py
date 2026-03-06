"""
Synthetic VRP data generator for Nairobi grocery delivery benchmark.

Generates orders, depots, and vehicles with realistic parameters.
Vary: order count, time window tightness, traffic multiplier, vehicle capacity
to prevent memorization and force algorithmic thinking.
"""

import json
import random
from dataclasses import dataclass, asdict
from typing import Literal

# Nairobi approximate bounds (lat, lon)
NAIROBI_LAT = (-1.35, -1.20)
NAIROBI_LON = (36.70, 37.00)

# Default depot locations (spread across Nairobi)
DEFAULT_DEPOTS = [
    {"id": 0, "lat": -1.2921, "lon": 36.7820},  # CBD
    {"id": 1, "lat": -1.3187, "lon": 36.8144},  # Westlands
    {"id": 2, "lat": -1.2677, "lon": 36.8060},  # Eastlands
]


@dataclass
class Order:
    order_id: int
    lat: float
    lon: float
    weight_kg: float
    window_start: float  # hours from midnight (e.g. 9.0 = 9:00)
    window_end: float
    late_penalty_per_min: float

    def to_dict(self):
        return asdict(self)


@dataclass
class Vehicle:
    vehicle_id: int
    capacity_kg: float
    start_depot_id: int
    fuel_cost_per_km: float
    wage_per_hour: float
    overtime_per_hour_after_8h: float

    def to_dict(self):
        return asdict(self)


def generate_orders(
    n: int,
    *,
    seed: int | None = None,
    weight_range: tuple[float, float] = (1.0, 25.0),
    window_tightness: Literal["loose", "medium", "tight"] = "medium",
    late_penalty_range: tuple[float, float] = (5.0, 50.0),
) -> list[dict]:
    """
    Generate n orders with random lat/lon in Nairobi bounds.
    window_tightness: loose (2h), medium (1h), tight (30min) windows.
    """
    rng = random.Random(seed)
    orders = []
    # Time window lengths in hours
    window_hours = {"loose": 2.0, "medium": 1.0, "tight": 0.5}
    wh = window_hours[window_tightness]
    # Start of day for windows (e.g. 6–16 so windows fall in operating day)
    day_start, day_end = 6.0, 16.0
    for i in range(n):
        lat = rng.uniform(*NAIROBI_LAT)
        lon = rng.uniform(*NAIROBI_LON)
        weight = rng.uniform(*weight_range)
        window_start = rng.uniform(day_start, day_end - wh)
        window_end = window_start + wh
        late_penalty = rng.uniform(*late_penalty_range)
        orders.append(
            Order(
                order_id=i,
                lat=lat,
                lon=lon,
                weight_kg=weight,
                window_start=round(window_start, 2),
                window_end=round(window_end, 2),
                late_penalty_per_min=round(late_penalty, 2),
            ).to_dict()
        )
    return orders


def generate_vehicles(
    num_vehicles: int,
    num_depots: int,
    *,
    seed: int | None = None,
    capacity_range: tuple[float, float] = (50.0, 150.0),
    fuel_cost_range: tuple[float, float] = (0.15, 0.35),
    wage_range: tuple[float, float] = (200.0, 400.0),
    overtime_multiplier: float = 1.5,
) -> list[dict]:
    """Each vehicle has capacity, start depot, fuel cost, wage, overtime cost."""
    rng = random.Random(seed)
    vehicles = []
    for i in range(num_vehicles):
        depot_id = rng.randint(0, num_depots - 1)
        wage = rng.uniform(*wage_range)
        vehicles.append(
            Vehicle(
                vehicle_id=i,
                capacity_kg=rng.uniform(*capacity_range),
                start_depot_id=depot_id,
                fuel_cost_per_km=round(rng.uniform(*fuel_cost_range), 3),
                wage_per_hour=round(wage, 2),
                overtime_per_hour_after_8h=round(wage * overtime_multiplier, 2),
            ).to_dict()
        )
    return vehicles


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate distance in km."""
    import math
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def get_traffic_multiplier(hour: float) -> float:
    """Rush hour 7–9 and 16–19 get 1.4; else 1.0."""
    if (7 <= hour < 9) or (16 <= hour < 19):
        return 1.4
    return 1.0


def generate_dataset(
    n_orders: int = 50,
    n_depots: int = 3,
    n_vehicles: int = 12,
    window_tightness: Literal["loose", "medium", "tight"] = "medium",
    seed: int | None = None,
) -> dict:
    """
    Full dataset: depots, orders, vehicles.
    Traffic rule: 1.0 off-peak, 1.4 rush (7–9, 16–19).
    """
    rng = random.Random(seed)
    depots = DEFAULT_DEPOTS[:n_depots]
    orders = generate_orders(n_orders, seed=seed, window_tightness=window_tightness)
    vehicles = generate_vehicles(n_vehicles, n_depots, seed=seed)
    return {
        "depots": depots,
        "orders": orders,
        "vehicles": vehicles,
        "traffic_rule": "1.0 off-peak; 1.4 for 7-9 and 16-19",
        "seed": seed,
    }


def dataset_to_json(dataset: dict) -> str:
    """Serialize for inclusion in prompt or file."""
    return json.dumps(dataset, indent=2)


def dataset_to_python_literal(dataset: dict) -> str:
    """As Python literal string for pasting into prompt."""
    return f"dataset = {json.dumps(dataset)}"
