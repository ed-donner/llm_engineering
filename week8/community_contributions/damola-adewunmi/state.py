"""
Shared state for the Deal Hunter LangGraph workflow.
"""

from typing import TypedDict


class DealHunterState(TypedDict, total=False):
    """State passed between Searcher → Valuer → Strategist."""

    # Input
    search_query: str

    # Searcher output: raw text from Tavily
    raw_search_results: str

    # Valuer output: list of structured deals from GPT-4o
    valued_deals: list[dict]

    # Strategist output: rows for Gradio Dataframe
    summary_table: list[list[str]]
    summary_message: str
