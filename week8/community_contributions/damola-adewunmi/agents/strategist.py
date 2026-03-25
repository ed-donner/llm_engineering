"""
Strategist Agent: summarize valued deals into a table for the Gradio UI.
"""

from typing import Any


def strategist_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Node: turn valued_deals into summary_table (list of rows) and a short message.
    """
    deals = state.get("valued_deals") or []
    rows = []
    for d in deals:
        retailer = d.get("retailer", "")
        denom = d.get("denomination_gbp", "")
        price = d.get("price_gbp", "")
        discount = d.get("discount_pct", "")
        verdict = d.get("verdict", "")
        url = d.get("url", "")
        rows.append([str(retailer), str(denom), str(price), str(discount), verdict, str(url)])
    n = len(rows)
    summary_message = (
        f"Found {n} PlayStation UK gift card deal(s). Strong Buy = discount >12%."
        if n else "No deals found from search results."
    )
    return {"summary_table": rows, "summary_message": summary_message}
