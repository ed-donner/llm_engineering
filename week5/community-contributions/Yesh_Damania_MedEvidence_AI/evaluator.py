import json
from pathlib import Path
import gradio as gr
import matplotlib.pyplot as plt
import pandas as pd


# Locate the saved evaluation results.
PROJECT_FOLDER = Path(__file__).resolve().parent
RESULTS_PATH = PROJECT_FOLDER / "evaluation" / "evaluation_results.json"


def load_results():
    """Load previously calculated evaluation scores."""
    if not RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Evaluation results not found: {RESULTS_PATH}"
        )

    with open(RESULTS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def make_chart(data, title):
    """Create a bar chart for a group of evaluation scores."""
    labels = list(data.keys())
    scores = list(data.values())

    fig, ax = plt.subplots(figsize=(8, 4))

    ax.bar(labels, scores)
    ax.set_title(title)
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.1)

    for i, score in enumerate(scores):
        ax.text(i, score + 0.02, f"{score:.3f}", ha="center")

    fig.tight_layout()
    return fig


def build_dashboard_data():
    """Prepare charts and tables from saved JSON results."""
    results = load_results()

    # TAB 1: Retrieval Evaluation
    retrieval = results["retrieval"]

    retrieval_scores = {
        "Hit Rate@5": retrieval["hit_rate_5"],
        "MRR@5": retrieval["mrr_5"],
        "nDCG@5": retrieval["ndcg_5"],
    }

    retrieval_chart = make_chart(
        retrieval_scores,
        "Semantic Search Retrieval Performance"
    )

    retrieval_table = pd.DataFrame([
        {"Metric": metric, "Score": score}
        for metric, score in retrieval_scores.items()
    ])

    # TAB 2: Answer Quality Evaluation
    quality = results["answer_quality"]

    quality_scores = {
        "Accuracy": quality["accuracy"],
        "Completeness": quality["completeness"],
        "Relevance": quality["relevance"],
    }

    quality_chart = make_chart(
        quality_scores,
        "LLM-Judged Answer Quality"
    )

    quality_table = pd.DataFrame([
        {"Metric": metric, "Score": score}
        for metric, score in quality_scores.items()
    ])

    # TAB 3: Retrieval Comparison
    comparison = results["retrieval_comparison"]

    comparison_table = pd.DataFrame({
        "Metric": ["Hit Rate@5", "MRR@5", "nDCG@5"],
        "Semantic Search": [
            comparison["semantic_search"]["hit_rate_5"],
            comparison["semantic_search"]["mrr_5"],
            comparison["semantic_search"]["ndcg_5"],
        ],
        "LLM Reranking": [
            comparison["llm_reranking"]["hit_rate_5"],
            comparison["llm_reranking"]["mrr_5"],
            comparison["llm_reranking"]["ndcg_5"],
        ],
    })

    comparison_chart = comparison_table.set_index("Metric").plot(
        kind="bar",
        figsize=(9, 4),
        rot=0,
        title="Semantic Search vs. LLM Reranking"
    ).get_figure()

    comparison_chart.axes[0].set_ylim(0, 1.1)
    comparison_chart.axes[0].set_ylabel("Average Score")
    comparison_chart.tight_layout()

    return (
        retrieval_chart,
        retrieval_table,
        quality_chart,
        quality_table,
        comparison_chart,
        comparison_table,
    )


# Build the Gradio interface.
with gr.Blocks(title="MedEvidence AI Evaluation") as app:

    gr.Markdown(
        """
        # MedEvidence AI — Evaluation Dashboard

        Evaluate research retrieval, answer quality,
        and the impact of LLM reranking.

        Scores are loaded from saved evaluation results.
        """
    )

    with gr.Tab("Retrieval Evaluation"):
        gr.Markdown("### Semantic Search Performance")
        retrieval_plot = gr.Plot()
        retrieval_df = gr.Dataframe(interactive=False)

    with gr.Tab("Answer Quality Evaluation"):
        gr.Markdown("### LLM-Judged Answer Quality")
        gr.Markdown(
            "These scores currently represent one evaluated answer."
        )
        quality_plot = gr.Plot()
        quality_df = gr.Dataframe(interactive=False)

    with gr.Tab("Retrieval Comparison"):
        gr.Markdown("### Semantic Search vs. LLM Reranking")
        gr.Markdown(
            "Comparison across five evaluation questions. "
            "Higher scores indicate better retrieval performance."
        )
        comparison_plot = gr.Plot()
        comparison_df = gr.Dataframe(interactive=False)

    refresh_button = gr.Button("Refresh Evaluation Results")

    # Load the saved metrics when the dashboard opens.
    app.load(
        fn=build_dashboard_data,
        outputs=[
            retrieval_plot,
            retrieval_df,
            quality_plot,
            quality_df,
            comparison_plot,
            comparison_df,
        ],
    )

    # Reload the JSON file when the button is clicked.
    refresh_button.click(
        fn=build_dashboard_data,
        outputs=[
            retrieval_plot,
            retrieval_df,
            quality_plot,
            quality_df,
            comparison_plot,
            comparison_df,
        ],
    )


if __name__ == "__main__":
    app.launch(inbrowser=True)
