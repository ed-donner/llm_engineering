import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Dict
import anthropic
from dotenv import load_dotenv

load_dotenv(override=True)


class TokenPredictor_Anthropic:
    def __init__(self, model_name: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic()
        self.model_name = model_name

    def predict_tokens(self, prompt: str, max_tokens: int = 100) -> List[Dict]:
        """
        Stream text from Claude and collect tokens.
        NOTE: Anthropic does not expose logprobs/top_logprobs, so probabilities
        and alternatives are not available. Each token is recorded with a
        placeholder probability of 1.0 and no alternatives.
        """
        predictions = []

        with self.client.messages.stream(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        ) as stream:
            for text in stream.text_stream:
                # Anthropic streams text chunks, not guaranteed single tokens,
                # but we treat each chunk as a unit (similar to a token group).
                prediction = {
                    "token": text,
                    "probability": 1.0,        # Not available via Anthropic API
                    "alternatives": [],         # Not available via Anthropic API
                }
                predictions.append(prediction)

        return predictions


def create_token_graph_Anthropic(model_name: str, predictions: List[Dict]) -> nx.DiGraph:
    """
    Create a directed graph showing token predictions.
    Alternatives are omitted since Anthropic doesn't provide logprobs.
    """
    G = nx.DiGraph()

    G.add_node("START", token=model_name, prob="START", color="lightgreen", size=4000)

    for i, pred in enumerate(predictions):
        token_id = f"t{i}"
        display_token = repr(pred["token"])  # Show whitespace/newlines clearly
        G.add_node(
            token_id,
            token=display_token,
            prob="N/A",   # Anthropic doesn't expose probabilities
            color="lightblue",
            size=6000,
        )
        prev = "START" if i == 0 else f"t{i - 1}"
        G.add_edge(prev, token_id)

        # Add any alternatives (will be empty for Anthropic)
        for j, (alt_token, alt_prob) in enumerate(pred["alternatives"]):
            alt_id = f"t{i}_alt{j}"
            G.add_node(
                alt_id,
                token=repr(alt_token),
                prob=f"{alt_prob * 100:.1f}%",
                color="lightgray",
                size=6000,
            )
            G.add_edge(prev, alt_id)

    last_main = f"t{len(predictions) - 1}" if predictions else "START"
    G.add_node("END", token="END", prob="100%", color="red", size=6000)
    G.add_edge(last_main, "END")

    return G


def visualize_predictions_Anthropic(G: nx.DiGraph, figsize=(14, 80)):
    """
    Visualize the token prediction graph with vertical layout.
    """
    plt.figure(figsize=figsize)

    spacing_y = 5
    spacing_x = 5

    main_nodes = [n for n in G.nodes() if "_alt" not in n]
    pos = {}
    for i, node in enumerate(main_nodes):
        pos[node] = (0, -i * spacing_y)

    for node in G.nodes():
        if "_alt" in node:
            main_token = node.split("_")[0]
            alt_num = int(node.split("_alt")[1])
            if main_token in pos:
                x_offset = -spacing_x if alt_num == 0 else spacing_x
                pos[node] = (x_offset, pos[main_token][1] + 0.05)

    node_colors = [G.nodes[node]["color"] for node in G.nodes()]
    node_sizes = [G.nodes[node]["size"] for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes)
    nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True, arrowsize=20, alpha=0.7)

    labels = {node: f"{G.nodes[node]['token']}\n{G.nodes[node]['prob']}" for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=14)

    plt.title("Token prediction (Anthropic Claude — no logprobs available)")
    plt.axis("off")

    margin = 8
    x_values = [x for x, y in pos.values()]
    y_values = [y for x, y in pos.values()]
    plt.xlim(min(x_values) - margin, max(x_values) + margin)
    plt.ylim(min(y_values) - margin, max(y_values) + margin)

    return plt

