"""
Gradio evaluation dashboard for Bugs RAG (inspired by week5/evaluator.py).
Run from Mikeaig4real: uv run python -m evals.evaluator
Or from notebook: from evals.evaluator import launch; launch()
"""

import sys
import logging
from pathlib import Path
from collections import defaultdict

import gradio as gr
import pandas as pd
from dotenv import load_dotenv
from gradio import Blocks, Button, Markdown, Checkbox

# Ensure Mikeaig4real is on path when run as script or from notebook
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.eval_runner import evaluate_all_retrieval
from evals.answer_eval import evaluate_all_answers

load_dotenv(override=True)

# Thresholds for color coding (same idea as week5 evaluator)
MRR_GREEN, MRR_AMBER = 0.9, 0.75
NDCG_GREEN, NDCG_AMBER = 0.9, 0.75
COVERAGE_GREEN, COVERAGE_AMBER = 90.0, 75.0
ANSWER_GREEN, ANSWER_AMBER = 4.5, 4.0


def _color(value: float, metric: str) -> str:
    if metric == "mrr":
        return (
            "green" if value >= MRR_GREEN else "orange" if value >= MRR_AMBER else "red"
        )
    if metric == "ndcg":
        return (
            "green"
            if value >= NDCG_GREEN
            else "orange" if value >= NDCG_AMBER else "red"
        )
    if metric == "coverage":
        return (
            "green"
            if value >= COVERAGE_GREEN
            else "orange" if value >= COVERAGE_AMBER else "red"
        )
    if metric in ("accuracy", "completeness", "relevance"):
        return (
            "green"
            if value >= ANSWER_GREEN
            else "orange" if value >= ANSWER_AMBER else "red"
        )
    return "black"


def _metric_html(
    label: str, value: float, metric: str, pct: bool = False, score_fmt: bool = False
) -> str:
    color = _color(value, metric)
    if pct:
        value_str = f"{value:.1f}%"
    elif score_fmt:
        value_str = f"{value:.2f}/5"
    else:
        value_str = f"{value:.4f}"
    return f"""
    <div style="margin: 10px 0; padding: 15px; background-color: #f5f5f5; border-radius: 8px; border-left: 5px solid {color};">
        <div style="font-size: 14px; color: #666; margin-bottom: 5px;">{label}</div>
        <div style="font-size: 28px; font-weight: bold; color: {color};">{value_str}</div>
    </div>
    """


def run_retrieval_eval(progress=gr.Progress()):
    """Run retrieval evaluation and return summary HTML + category bar chart."""
    global stop_retrieval_eval
    stop_retrieval_eval = False
    total_mrr = total_ndcg = total_cov = 0.0
    count = 0
    by_cat = defaultdict(list)

    for test, result, prog in evaluate_all_retrieval():
        if stop_retrieval_eval:
            logging.warning("[LOG] Retrieval evaluation stopped by user.")
            break
        count += 1
        total_mrr += result.mrr
        total_ndcg += result.ndcg
        total_cov += result.keyword_coverage
        by_cat[test.category].append(result.mrr)
        progress(prog, desc=f"Retrieval eval {count}...")

    if count == 0:
        return (
            "<div style='padding:20px;color:#999'>No tests found. Add evals/tests.jsonl.</div>",
            pd.DataFrame(),
        )

    avg_mrr = total_mrr / count
    avg_ndcg = total_ndcg / count
    avg_cov = total_cov / count

    html = f"""
    <div style="padding: 0;">
        {_metric_html("Mean Reciprocal Rank (MRR)", avg_mrr, "mrr")}
        {_metric_html("Normalized DCG (nDCG)", avg_ndcg, "ndcg")}
        {_metric_html("Keyword Coverage", avg_cov, "coverage", pct=True)}
        <div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border-radius: 5px; text-align: center; border: 1px solid #c3e6cb;">
            <span style="font-size: 14px; color: #155724; font-weight: bold;">✓ Retrieval evaluation complete: {count} tests</span>
        </div>
    </div>
    """
    df = pd.DataFrame(
        [
            {"Category": cat, "Average MRR": sum(s) / len(s)}
            for cat, s in sorted(by_cat.items())
        ]
    )
    return html, df


def run_answer_eval(progress=gr.Progress()):
    """Run answer evaluation (RAG + LLM judge) and return summary HTML + category chart."""
    global stop_answer_eval
    stop_answer_eval = False
    total_acc = total_comp = total_rel = 0.0
    count = 0
    by_cat = defaultdict(list)

    for test, result, prog in evaluate_all_answers():
        if stop_answer_eval:
            logging.warning("[LOG] Answer evaluation stopped by user.")
            break
        count += 1
        total_acc += result.accuracy
        total_comp += result.completeness
        total_rel += result.relevance
        by_cat[test.category].append(result.accuracy)
        progress(prog, desc=f"Answer eval {count}...")

    if count == 0:
        return (
            "<div style='padding:20px;color:#999'>No tests found.</div>",
            pd.DataFrame(),
        )

    avg_acc = total_acc / count
    avg_comp = total_comp / count
    avg_rel = total_rel / count

    html = f"""
    <div style="padding: 0;">
        {_metric_html("Accuracy", avg_acc, "accuracy", score_fmt=True)}
        {_metric_html("Completeness", avg_comp, "completeness", score_fmt=True)}
        {_metric_html("Relevance", avg_rel, "relevance", score_fmt=True)}
        <div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border-radius: 5px; text-align: center; border: 1px solid #c3e6cb;">
            <span style="font-size: 14px; color: #155724; font-weight: bold;">✓ Answer evaluation complete: {count} tests</span>
        </div>
    </div>
    """
    df = pd.DataFrame(
        [
            {"Category": cat, "Average Accuracy": sum(s) / len(s)}
            for cat, s in sorted(by_cat.items())
        ]
    )
    return html, df


def launch(inbrowser: bool = True):
    """Build and launch the Gradio evaluation app."""
    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    # Set up logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    # Log tracker toggle state (shared between modules)
    def set_log_tracker(enabled):
        import evals.eval_runner, evals.answer_eval

        evals.eval_runner.LOG_TRACKER_ENABLED = enabled
        evals.answer_eval.LOG_TRACKER_ENABLED = enabled
        return f"Log tracker is {'ON' if enabled else 'OFF'}"

    # Stop flags for evals
    global stop_retrieval_eval, stop_answer_eval
    stop_retrieval_eval = False
    stop_answer_eval = False

    def stop_retrieval():
        global stop_retrieval_eval
        stop_retrieval_eval = True
        return "Retrieval evaluation stopped."

    def stop_answer():
        global stop_answer_eval
        stop_answer_eval = True
        return "Answer evaluation stopped."

    with Blocks(title="Bugs RAG Evaluation Dashboard", theme=theme) as app:
        Markdown("# Bugs RAG Evaluation Dashboard")
        Markdown(
            "Evaluate retrieval (MRR, nDCG, keyword coverage) and answer quality (accuracy, completeness, relevance) for the bugs knowledge base."
        )

        with gr.Row():
            log_toggle = Checkbox(
                label="Enable log tracker (debug context/answer process)", value=False
            )
            log_status = Markdown("Log tracker is OFF")
            log_toggle.change(fn=set_log_tracker, inputs=log_toggle, outputs=log_status)

        # Stop buttons
        with gr.Row():
            stop_retrieval_btn = Button("Stop Retrieval Eval", variant="stop")
            stop_answer_btn = Button("Stop Answer Eval", variant="stop")
            stop_retrieval_msg = Markdown(visible=False)
            stop_answer_msg = Markdown(visible=False)
            stop_retrieval_btn.click(fn=stop_retrieval, outputs=stop_retrieval_msg)
            stop_answer_btn.click(fn=stop_answer, outputs=stop_answer_msg)

        gr.Markdown("## Retrieval evaluation")
        retrieval_btn = gr.Button(
            "Run retrieval evaluation", variant="primary", size="lg"
        )
        with gr.Row():
            retrieval_metrics = gr.HTML(
                "<div style='padding: 20px; text-align: center; color: #999;'>Click the button to run</div>"
            )
            retrieval_chart = gr.BarPlot(
                x="Category",
                y="Average MRR",
                title="Average MRR by category",
                y_lim=[0, 1],
                height=400,
            )
        retrieval_btn.click(
            fn=run_retrieval_eval,
            outputs=[retrieval_metrics, retrieval_chart],
        )

        gr.Markdown("## Answer evaluation (RAG + LLM judge)")
        answer_btn = gr.Button("Run answer evaluation", variant="primary", size="lg")
        with gr.Row():
            answer_metrics = gr.HTML(
                "<div style='padding: 20px; text-align: center; color: #999;'>Click the button to run</div>"
            )
            answer_chart = gr.BarPlot(
                x="Category",
                y="Average Accuracy",
                title="Average accuracy by category",
                y_lim=[1, 5],
                height=400,
            )
        answer_btn.click(
            fn=run_answer_eval,
            outputs=[answer_metrics, answer_chart],
        )

    app.launch(inbrowser=inbrowser)


def main():
    launch(inbrowser=True)


if __name__ == "__main__":
    main()
