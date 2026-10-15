"""
Gradio dashboard for evaluating the Hospital-Ashir RAG system.

Runs the retrieval and answer evaluations from `evaluation/eval.py` and
displays MRR / nDCG / keyword coverage and LLM-as-judge answer scores with
colour-coded metric cards and per-category bar charts.

Launch:
    python evaluator.py
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import gradio as gr
import pandas as pd
from dotenv import load_dotenv

# Make the local `evaluation/` package importable when running from any cwd.
BASE_DIR = Path(__file__).parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from evaluation.eval import evaluate_all_retrieval, evaluate_all_answers  # noqa: E402


load_dotenv(override=True)


# ---------------------------------------------------------------------------
# Colour thresholds
# ---------------------------------------------------------------------------

# Retrieval (0-1 scale, coverage 0-100)
MRR_GREEN = 0.90
MRR_AMBER = 0.75
NDCG_GREEN = 0.90
NDCG_AMBER = 0.75
COVERAGE_GREEN = 90.0
COVERAGE_AMBER = 75.0

# Answer quality (1-5 scale)
ANSWER_GREEN = 4.5
ANSWER_AMBER = 4.0


def get_color(value: float, metric_type: str) -> str:
    """Pick a colour for a metric value based on its type and thresholds."""
    if metric_type == "mrr":
        return "green" if value >= MRR_GREEN else "orange" if value >= MRR_AMBER else "red"
    if metric_type == "ndcg":
        return "green" if value >= NDCG_GREEN else "orange" if value >= NDCG_AMBER else "red"
    if metric_type == "coverage":
        return (
            "green"
            if value >= COVERAGE_GREEN
            else "orange"
            if value >= COVERAGE_AMBER
            else "red"
        )
    if metric_type in {"accuracy", "completeness", "relevance"}:
        return (
            "green"
            if value >= ANSWER_GREEN
            else "orange"
            if value >= ANSWER_AMBER
            else "red"
        )
    return "black"


def format_metric_html(
    label: str,
    value: float,
    metric_type: str,
    is_percentage: bool = False,
    score_format: bool = False,
) -> str:
    """Render one metric card as HTML."""
    color = get_color(value, metric_type)
    if is_percentage:
        value_str = f"{value:.1f}%"
    elif score_format:
        value_str = f"{value:.2f}/5"
    else:
        value_str = f"{value:.4f}"
    return f"""
    <div style="margin: 10px 0; padding: 15px; background-color: #f5f5f5; border-radius: 8px; border-left: 5px solid {color};">
        <div style="font-size: 14px; color: #666; margin-bottom: 5px;">{label}</div>
        <div style="font-size: 28px; font-weight: bold; color: {color};">{value_str}</div>
    </div>
    """


# ---------------------------------------------------------------------------
# Evaluation runners (called from Gradio buttons)
# ---------------------------------------------------------------------------

def run_retrieval_evaluation(progress=gr.Progress()):
    """Run retrieval evaluation across every test and return summary + chart data."""
    total_mrr = 0.0
    total_ndcg = 0.0
    total_coverage = 0.0
    category_mrr: dict[str, list[float]] = defaultdict(list)
    count = 0

    for test, result, prog_value in evaluate_all_retrieval():
        count += 1
        total_mrr += result.mrr
        total_ndcg += result.ndcg
        total_coverage += result.keyword_coverage
        category_mrr[test.category].append(result.mrr)
        progress(prog_value, desc=f"Evaluating retrieval test {count}...")

    avg_mrr = total_mrr / count if count else 0.0
    avg_ndcg = total_ndcg / count if count else 0.0
    avg_coverage = total_coverage / count if count else 0.0

    final_html = f"""
    <div style="padding: 0;">
        {format_metric_html("Mean Reciprocal Rank (MRR)", avg_mrr, "mrr")}
        {format_metric_html("Normalized DCG (nDCG)", avg_ndcg, "ndcg")}
        {format_metric_html("Keyword Coverage", avg_coverage, "coverage", is_percentage=True)}
        <div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border-radius: 5px; text-align: center; border: 1px solid #c3e6cb;">
            <span style="font-size: 14px; color: #155724; font-weight: bold;">✓ Evaluation Complete: {count} tests</span>
        </div>
    </div>
    """

    category_data = [
        {"Category": category, "Average MRR": sum(scores) / len(scores)}
        for category, scores in category_mrr.items()
    ]
    df = pd.DataFrame(category_data)
    return final_html, df


def run_answer_evaluation(progress=gr.Progress()):
    """Run LLM-as-judge answer evaluation across every test."""
    total_accuracy = 0.0
    total_completeness = 0.0
    total_relevance = 0.0
    category_accuracy: dict[str, list[float]] = defaultdict(list)
    count = 0

    for test, result, prog_value in evaluate_all_answers():
        count += 1
        total_accuracy += result.accuracy
        total_completeness += result.completeness
        total_relevance += result.relevance
        category_accuracy[test.category].append(result.accuracy)
        progress(prog_value, desc=f"Evaluating answer test {count}...")

    avg_accuracy = total_accuracy / count if count else 0.0
    avg_completeness = total_completeness / count if count else 0.0
    avg_relevance = total_relevance / count if count else 0.0

    final_html = f"""
    <div style="padding: 0;">
        {format_metric_html("Accuracy", avg_accuracy, "accuracy", score_format=True)}
        {format_metric_html("Completeness", avg_completeness, "completeness", score_format=True)}
        {format_metric_html("Relevance", avg_relevance, "relevance", score_format=True)}
        <div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border-radius: 5px; text-align: center; border: 1px solid #c3e6cb;">
            <span style="font-size: 14px; color: #155724; font-weight: bold;">✓ Evaluation Complete: {count} tests</span>
        </div>
    </div>
    """

    category_data = [
        {"Category": category, "Average Accuracy": sum(scores) / len(scores)}
        for category, scores in category_accuracy.items()
    ]
    df = pd.DataFrame(category_data)
    return final_html, df


# ---------------------------------------------------------------------------
# Gradio app
# ---------------------------------------------------------------------------

def main() -> None:
    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    intro_md = (
        "# Ashir General Hospital — RAG Evaluation Dashboard\n\n"
        "Evaluate retrieval and answer quality for the **Hospital-Ashir** "
        "knowledge base (hospital, doctors, patients, and disease programs).\n\n"
        "*Run `python ingest.py` first to build the vector database.*"
    )

    with gr.Blocks(title="Hospital-Ashir RAG Evaluation", theme=theme) as app:
        gr.Markdown(intro_md)

        # ---------- Retrieval section ----------
        gr.Markdown("## Retrieval Evaluation")
        gr.Markdown(
            "Scores the vector store on Mean Reciprocal Rank, nDCG, and keyword "
            "coverage against 47 curated test questions covering doctors, patients, "
            "diseases, and hospital facilities."
        )

        retrieval_button = gr.Button(
            "Run Retrieval Evaluation", variant="primary", size="lg"
        )

        with gr.Row():
            with gr.Column(scale=1):
                retrieval_metrics = gr.HTML(
                    "<div style='padding: 20px; text-align: center; color: #999;'>"
                    "Click 'Run Retrieval Evaluation' to start"
                    "</div>"
                )
            with gr.Column(scale=1):
                retrieval_chart = gr.BarPlot(
                    x="Category",
                    y="Average MRR",
                    title="Average MRR by Category",
                    y_lim=[0, 1],
                    height=400,
                )

        # ---------- Answer section ----------
        gr.Markdown("## Answer Evaluation")
        gr.Markdown(
            "Uses an LLM judge (`gpt-4.1-nano`) to score each generated answer on "
            "accuracy, completeness, and relevance against the reference answer. "
            "This makes one LLM call per test — it is the slower and more "
            "expensive of the two evaluations."
        )

        answer_button = gr.Button(
            "Run Answer Evaluation", variant="primary", size="lg"
        )

        with gr.Row():
            with gr.Column(scale=1):
                answer_metrics = gr.HTML(
                    "<div style='padding: 20px; text-align: center; color: #999;'>"
                    "Click 'Run Answer Evaluation' to start"
                    "</div>"
                )
            with gr.Column(scale=1):
                answer_chart = gr.BarPlot(
                    x="Category",
                    y="Average Accuracy",
                    title="Average Accuracy by Category",
                    y_lim=[1, 5],
                    height=400,
                )

        retrieval_button.click(
            fn=run_retrieval_evaluation,
            outputs=[retrieval_metrics, retrieval_chart],
        )
        answer_button.click(
            fn=run_answer_evaluation,
            outputs=[answer_metrics, answer_chart],
        )

    app.launch(inbrowser=True)


if __name__ == "__main__":
    main()
