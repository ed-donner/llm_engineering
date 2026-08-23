# ------------------------------------------------------------
#  token_graph_groq_no_logprobs.py
# ------------------------------------------------------------
import os
import math
from typing import List, Dict

import networkx as nx
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# ------------------------------------------------------------------
# 1️⃣  Import Groq client
# ------------------------------------------------------------------
from groq import Groq   # <-- Groq SDK

load_dotenv(override=True)   # expects GROQ_API_KEY in .env

# ------------------------------------------------------------------
# 2️⃣  TokenPredictor – now **without** logprobs
# ------------------------------------------------------------------
class TokenPredictor_Groq:
    """
    Calls a Groq model and returns a simple list of tokens.
    Because Groq does not provide log‑probabilities, each token gets
    a dummy probability of 1.0 and an empty alternatives list.
    """

    def __init__(self, model_name: str):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model_name = model_name

    def predict_tokens(self, prompt: str, max_tokens: int = 100) -> List[Dict]:
        """
        Stream the completion token‑by‑token.
        Returns a list of dicts that match the shape expected by the
        graph‑building code, but with placeholder probabilities.
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.0,          # deterministic output
            stream=True,              # we still stream token‑by‑token
        )

        predictions: List[Dict] = []

        for chunk in response:
            # Some chunks are just keep‑alive signals – ignore them
            if not chunk.choices[0].delta.content:
                continue

            token = chunk.choices[0].delta.content

            # Because we have no log‑probs, we fake a probability of 1.0
            # and provide an empty alternatives list.
            predictions.append(
                {
                    "token": token,
                    "probability": 1.0,          # dummy – will be shown as 100%
                    "alternatives": [],          # no alternatives available
                }
            )
        return predictions


# ------------------------------------------------------------------
# 3️⃣  Graph‑building helpers (unchanged – they just ignore empty alternatives)
# ------------------------------------------------------------------
def create_token_graph_Groq(model_name: str, predictions: List[Dict]) -> nx.DiGraph:
    G = nx.DiGraph()

    G.add_node(
        "START",
        token=model_name,
        prob="START",
        color="lightgreen",
        size=4000,
    )

    # Main token chain
    for i, pred in enumerate(predictions):
        token_id = f"t{i}"
        G.add_node(
            token_id,
            token=pred["token"],
            prob=f"{pred['probability'] * 100:.1f}%",
            color="lightblue",
            size=6000,
        )
        if i == 0:
            G.add_edge("START", token_id)
        else:
            G.add_edge(f"t{i-1}", token_id)

    # Alternative nodes – will be skipped because the list is empty
    for i, pred in enumerate(predictions):
        parent = "START" if i == 0 else f"t{i-1}"
        for j, (alt_tok, alt_prob) in enumerate(pred["alternatives"]):
            alt_id = f"t{i}_alt{j}"
            G.add_node(
                alt_id,
                token=alt_tok,
                prob=f"{alt_prob * 100:.1f}%",
                color="lightgray",
                size=6000,
            )
            G.add_edge(parent, alt_id)

    # END node – connect to the last *main* token (or START if nothing)
    final_main = f"t{len(predictions)-1}" if predictions else "START"
    G.add_node(
        "END",
        token="END",
        prob="100%",
        color="red",
        size=6000,
    )
    G.add_edge(final_main, "END")

    return G


def visualize_predictions_Groq(G: nx.DiGraph, figsize=(14, 80)):
    plt.figure(figsize=figsize)

    # ---- positioning -------------------------------------------------
    pos = {}
    spacing_y = 5
    spacing_x = 5

    main_nodes = [n for n in G.nodes if "_alt" not in n]
    for i, node in enumerate(main_nodes):
        pos[node] = (0, -i * spacing_y)

    for node in G.nodes:
        if "_alt" in node:
            parent = node.split("_")[0]
            alt_num = int(node.split("_alt")[1])
            x_offset = -spacing_x if alt_num == 0 else spacing_x
            pos[node] = (x_offset, pos[parent][1] + 0.05)

    # ---- drawing -----------------------------------------------------
    node_colors = [G.nodes[n]["color"] for n in G.nodes]
    node_sizes  = [G.nodes[n]["size"]  for n in G.nodes]

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes)
    nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True,
                           arrowsize=20, alpha=0.7)

    labels = {n: f"{G.nodes[n]['token']}\n{G.nodes[n]['prob']}" for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels, font_size=14)

    plt.title("Token prediction graph (Groq – no logprobs)")
    plt.axis("off")

    # make sure everything fits
    margin = 8
    xs, ys = zip(*pos.values())
    plt.xlim(min(xs) - margin, max(xs) + margin)
    plt.ylim(min(ys) - margin, max(ys) + margin)

    return plt