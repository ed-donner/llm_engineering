import gradio as gr
import numpy as np
import pandas as pd
import plotly.express as px
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from dotenv import load_dotenv

load_dotenv(override=True)

MODELS = {
    "all-MiniLM-L6-v2 (fast, 384-dim)": "all-MiniLM-L6-v2",
    "all-mpnet-base-v2 (accurate, 768-dim)": "all-mpnet-base-v2",
    "paraphrase-MiniLM-L3-v2 (tiny, 384-dim)": "paraphrase-MiniLM-L3-v2",
    "BAAI/bge-small-en-v1.5 (retrieval-tuned)": "BAAI/bge-small-en-v1.5",
}

_model_cache: dict = {}


def _load_model(model_id: str) -> SentenceTransformer:
    if model_id not in _model_cache:
        _model_cache[model_id] = SentenceTransformer(model_id)
    return _model_cache[model_id]


def _parse_lines(text: str) -> list[str]:
    return [line.strip() for line in text.strip().splitlines() if line.strip()]


def visualize(sentences_text: str, labels_text: str, model_key: str, method: str, dims: str):
    sentences = _parse_lines(sentences_text)
    if len(sentences) < 3:
        return None, "Enter at least 3 sentences."

    raw_labels = _parse_lines(labels_text) if labels_text.strip() else None
    if raw_labels and len(raw_labels) != len(sentences):
        return None, (
            f"Label count ({len(raw_labels)}) doesn't match sentence count ({len(sentences)}). "
            "Fix the labels or leave the field blank."
        )

    model = _load_model(MODELS[model_key])
    embeddings = model.encode(sentences, show_progress_bar=False, normalize_embeddings=True)

    n = int(dims[0])  # "2D" -> 2, "3D" -> 3
    n_components = min(n, len(sentences) - 1, embeddings.shape[1])

    if method == "PCA":
        coords = PCA(n_components=n_components, random_state=42).fit_transform(embeddings)
    else:
        perplexity = min(30, max(5, len(sentences) // 2))
        coords = TSNE(n_components=n_components, perplexity=perplexity, random_state=42).fit_transform(embeddings)

    # Pad to 3 columns so the 3-D branch always has z
    if coords.shape[1] < 3:
        coords = np.hstack([coords, np.zeros((len(coords), 3 - coords.shape[1]))])

    df = pd.DataFrame({
        "x": coords[:, 0],
        "y": coords[:, 1],
        "z": coords[:, 2],
        "label": raw_labels if raw_labels else ["(unlabeled)"] * len(sentences),
        "text": [s[:100] + ("…" if len(s) > 100 else "") for s in sentences],
    })

    shared_kwargs = dict(
        color="label",
        hover_name="text",
        hover_data={"x": False, "y": False, "z": False, "label": True},
        title=f"Sentence Embedding Space  ·  {model_key.split('(')[0].strip()}  ·  {method} → {n}D",
        height=620,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    if n == 2:
        fig = px.scatter(df, x="x", y="y", **shared_kwargs)
        fig.update_traces(marker_size=11)
    else:
        fig = px.scatter_3d(df, x="x", y="y", z="z", **shared_kwargs)
        fig.update_traces(marker_size=6)

    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="#f8f9fa",
        font_size=13,
        legend_title_text="Label",
    )

    return fig, f"Embedded {len(sentences)} sentences with {model_key.split('(')[0].strip()}."


# ── Default demo data ────────────────────────────────────────────────────────

DEFAULT_SENTENCES = """\
The cat sat on the mat.
A dog is running through the park.
Transformers revolutionised natural language processing.
BERT uses bidirectional attention to understand context.
Paris is the capital of France.
Berlin sits at the heart of Europe.
The stock market tumbled on inflation fears.
Investors are watching interest-rate decisions closely.
I love cooking Italian food on weekends.
Sushi is my favourite Japanese dish.
The astronaut floated weightlessly in the cabin.
The rocket launched at dawn from Cape Canaveral."""

DEFAULT_LABELS = """\
animals
animals
AI/ML
AI/ML
geography
geography
finance
finance
food
food
space
space"""

# ── Gradio UI ────────────────────────────────────────────────────────────────

with gr.Blocks(title="Sentence Embedding Visualizer", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# Sentence Embedding Visualizer\n"
        "Encode sentences with a Hugging Face model and explore their geometry in 2D or 3D space."
    )

    with gr.Row():
        with gr.Column(scale=1, min_width=320):
            sentences_box = gr.Textbox(
                label="Sentences  (one per line, minimum 3)",
                lines=14,
                value=DEFAULT_SENTENCES,
            )
            labels_box = gr.Textbox(
                label="Labels  (optional, one per line — must match sentence count)",
                lines=14,
                value=DEFAULT_LABELS,
                placeholder="Leave blank to colour all points the same.",
            )
            with gr.Group():
                model_dd = gr.Dropdown(
                    choices=list(MODELS.keys()),
                    value="all-MiniLM-L6-v2 (fast, 384-dim)",
                    label="Embedding model",
                )
                with gr.Row():
                    method_radio = gr.Radio(
                        choices=["PCA", "t-SNE"],
                        value="PCA",
                        label="Reduction method",
                        info="PCA is deterministic & fast; t-SNE reveals local clusters.",
                    )
                    dims_radio = gr.Radio(
                        choices=["2D", "3D"],
                        value="2D",
                        label="Dimensions",
                    )
            run_btn = gr.Button("Visualize embeddings", variant="primary", size="lg")
            status_box = gr.Textbox(label="Status", interactive=False, lines=1)

        with gr.Column(scale=2):
            plot = gr.Plot(label="Embedding space")

    run_btn.click(
        fn=visualize,
        inputs=[sentences_box, labels_box, model_dd, method_radio, dims_radio],
        outputs=[plot, status_box],
    )

if __name__ == "__main__":
    demo.launch()
