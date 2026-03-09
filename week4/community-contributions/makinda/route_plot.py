"""
Optional route visualization: plot depots, orders, and vehicle routes.
"""

from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def plot_routes(dataset: dict, result: dict | None) -> plt.Figure:
    """
    Plot depots (triangles), orders (dots), and routes (lines) if result has 'routes'.
    Returns matplotlib Figure; if no routes, returns a small figure with a message.
    """
    if not result or not result.get("routes"):
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, "No routes to display", ha="center", va="center")
        return fig
    depots = dataset.get("depots", [])
    orders = {o["order_id"]: (o["lat"], o["lon"]) for o in dataset.get("orders", [])}
    vehicles = dataset.get("vehicles", [])
    fig, ax = plt.subplots(figsize=(10, 8))
    # Depots
    for d in depots:
        ax.scatter(d["lon"], d["lat"], marker="^", s=200, label=f"Depot {d['id']}", zorder=5)
    # Orders
    if orders:
        lats = [o[0] for o in orders.values()]
        lons = [o[1] for o in orders.values()]
        ax.scatter(lons, lats, c="gray", s=20, alpha=0.7, label="Orders")
    # Routes
    colors = plt.cm.tab10.colors
    for vid, route in enumerate(result["routes"]):
        if not route:
            continue
        color = colors[vid % len(colors)]
        depot = next((d for d in depots if d["id"] == vehicles[vid]["start_depot_id"]), depots[0])
        xs, ys = [depot["lon"]], [depot["lat"]]
        for oid in route:
            if oid in orders:
                xs.append(orders[oid][1])
                ys.append(orders[oid][0])
        xs.append(depot["lon"])
        ys.append(depot["lat"])
        ax.plot(xs, ys, color=color, alpha=0.7, label=f"V{vid}")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Delivery routes")
    ax.legend(loc="upper left", fontsize=6)
    ax.set_aspect("equal")
    plt.tight_layout()
    return fig
