"""
Deal Hunter multi-agent workflow using LangGraph.
Searcher → Valuer → Strategist.
"""

from langgraph.graph import END, StateGraph
from state import DealHunterState
from agents.searcher import searcher_node
from agents.valuer import valuer_node
from agents.strategist import strategist_node


def build_graph():
    """Build and compile the Deal Hunter graph."""
    graph = StateGraph(DealHunterState)

    graph.add_node("searcher", searcher_node)
    graph.add_node("valuer", valuer_node)
    graph.add_node("strategist", strategist_node)

    graph.set_entry_point("searcher")
    graph.add_edge("searcher", "valuer")
    graph.add_edge("valuer", "strategist")
    graph.add_edge("strategist", END)

    return graph.compile()


# Singleton compiled graph for the app
_deal_hunter_graph = None


def get_graph():
    global _deal_hunter_graph
    if _deal_hunter_graph is None:
        _deal_hunter_graph = build_graph()
    return _deal_hunter_graph


def run_deal_hunter(search_query: str = "") -> dict:
    """
    Run the full pipeline and return final state (including summary_table and summary_message).
    """
    g = get_graph()
    initial: DealHunterState = {"search_query": search_query or ""}
    result = g.invoke(initial)
    return result
