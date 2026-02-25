import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Dict
from dotenv import load_dotenv
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login

load_dotenv(override=True)
hf_token = os.environ.get("HF_TOKEN")

class TokenPredictor_HF:
    def __init__(self, model_name: str):
        # ---- Hugging Face login ----
        login(token=hf_token, add_to_git_credential=True)

        self.model_name = model_name

        # ---- Select device (Apple Silicon aware) ----
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

        # ---- Load tokenizer ----
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        # ---- Load model (float32 is safest on MPS) ----
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
        ).to(self.device)

        self.model.eval()

    def predict_tokens(self, prompt: str, max_tokens: int = 50) -> List[Dict]:
        """
        Generate tokens and capture top-3 probabilities per generation step.
        """

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,               # deterministic (like temperature=0)
                return_dict_in_generate=True,
                output_scores=True,
            )

        # Generated token IDs (excluding prompt)
        generated_ids = output.sequences[0][inputs["input_ids"].shape[1]:]
        scores = output.scores  # one logits tensor per generated token

        predictions = []

        for token_id, logits in zip(generated_ids, scores):
            # logits shape: [1, vocab_size]
            probs = torch.softmax(logits[0], dim=-1)

            top_probs, top_ids = torch.topk(probs, k=3)

            top_token = self.tokenizer.decode(top_ids[0])
            top_prob = top_probs[0].item()

            alternatives = []
            for i in range(1, 3):
                alternatives.append(
                    (
                        self.tokenizer.decode(top_ids[i]),
                        top_probs[i].item(),
                    )
                )

            predictions.append(
                {
                    "token": top_token,
                    "probability": top_prob,
                    "alternatives": alternatives,
                }
            )

        return predictions


def create_token_graph_HF(model_name: str, predictions: List[Dict]) -> nx.DiGraph:
    """
    Create a directed graph showing token predictions and alternatives.
    """
    G = nx.DiGraph()

    G.add_node("START", token=model_name, prob="START", color="lightgreen", size=4000)

    # First, create all main token nodes in sequence
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
            G.add_edge(f"t{i - 1}", token_id)

    # Then add alternative nodes with a different y-position
    last_id = None
    for i, pred in enumerate(predictions):
        parent_token = "START" if i == 0 else f"t{i - 1}"

        # Add alternative token nodes slightly below main sequence
        for j, (alt_token, alt_prob) in enumerate(pred["alternatives"]):
            alt_id = f"t{i}_alt{j}"
            G.add_node(
                alt_id, token=alt_token, prob=f"{alt_prob * 100:.1f}%", color="lightgray", size=6000
            )

            # Add edge from main token to its alternatives only
            G.add_edge(parent_token, alt_id)
            last_id = parent_token

    G.add_node("END", token="END", prob="100%", color="red", size=6000)
    G.add_edge(last_id, "END")

    return G


def visualise_predictions_HF(G: nx.DiGraph, figsize=(14, 80)):
    """
    Visualise the token prediction graph with vertical layout and alternating alternatives.
    """
    plt.figure(figsize=figsize)

    # Create custom positioning for nodes
    pos = {}
    spacing_y = 5  # Vertical spacing between main tokens
    spacing_x = 5  # Horizontal spacing for alternatives

    # Position main token nodes in a vertical line
    main_nodes = [n for n in G.nodes() if "_alt" not in n]
    for i, node in enumerate(main_nodes):
        pos[node] = (0, -i * spacing_y)  # Center main tokens vertically

    # Position alternative nodes to left and right of main tokens
    for node in G.nodes():
        if "_alt" in node:
            main_token = node.split("_")[0]
            alt_num = int(node.split("_alt")[1])
            if main_token in pos:
                # Place first alternative to left, second to right
                x_offset = -spacing_x if alt_num == 0 else spacing_x
                pos[node] = (x_offset, pos[main_token][1] + 0.05)

    # Draw nodes
    node_colors = [G.nodes[node]["color"] for node in G.nodes()]
    node_sizes = [G.nodes[node]["size"] for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes)

    # Draw all edges as straight lines
    nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True, arrowsize=20, alpha=0.7)

    # Add labels with token and probability
    labels = {node: f"{G.nodes[node]['token']}\n{G.nodes[node]['prob']}" for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=14)

    plt.title("Token prediction.")
    plt.axis("off")

    # Adjust plot limits to ensure all nodes are visible
    margin = 8
    x_values = [x for x, y in pos.values()]
    y_values = [y for x, y in pos.values()]
    plt.xlim(min(x_values) - margin, max(x_values) + margin)
    plt.ylim(min(y_values) - margin, max(y_values) + margin)

    # plt.tight_layout()
    return plt