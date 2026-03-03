import gradio as gr
import pandas as pd
from collections import defaultdict
from dotenv import load_dotenv

from evaluation.eval import evaluate_all_retrieval, evaluate_all_answers

load_dotenv(override=True)

# Color thresholds
MRR_GREEN = 0.9
MRR_AMBER = 0.75
NDCG_GREEN = 0.9
NDCG_AMBER = 0.75
COVERAGE_GREEN = 90.0
COVERAGE_AMBER = 75.0

ANSWER_GREEN = 4.5
ANSWER_AMBER = 4.0


def get_color(value: float, metric_type: str) -> str:
    if metric_type == "mrr":
        if value >= MRR_GREEN:      return "green"
        if value >= MRR_AMBER:      return "orange"
        return "red"
    if metric_type == "ndcg":
        if value >= NDCG_GREEN:     return "green"
        if value >= NDCG_AMBER:     return "orange"
        return "red"
    if metric_type == "coverage":
        if value >= COVERAGE_GREEN: return "green"
        if value >= COVERAGE_AMBER: return "orange"
        return "red"
    if metric_type in ("accuracy", "completeness", "relevance"):
        if value >= ANSWER_GREEN:   return "green"
        if value >= ANSWER_AMBER:   return "orange"
        return "red"
    return "black"


def format_metric_html(
    label: str,
    value: float,
    metric_type: str,
    is_percentage: bool = False,
    score_format: bool = False,
) -> str:
    color = get_color(value, metric_type)
    if is_percentage:
        value_str = f"{value:.1f}%"
    elif score_format:
        value_str = f"{value:.2f}/5"
    else:
        value_str = f"{value:.4f}"
    return f"""
    <div style="margin:10px 0;padding:15px;background:#f5f5f5;border-radius:8px;border-left:5px solid {color};">
        <div style="font-size:14px;color:#666;margin-bottom:5px;">{label}</div>
        <div style="font-size:28px;font-weight:bold;color:{color};">{value_str}</div>
    </div>
    """


# Retrieval

def run_retrieval_evaluation(progress=gr.Progress()):
    total_mrr = total_ndcg = total_coverage = 0.0
    category_mrr: dict[str, list[float]] = defaultdict(list)
    count = 0

    for test, result, prog_value in evaluate_all_retrieval():
        count += 1
        total_mrr      += result.mrr
        total_ndcg     += result.ndcg
        total_coverage += result.keyword_coverage
        category_mrr[test.category].append(result.mrr)
        progress(prog_value, desc=f"Evaluating test {count}...")

    avg_mrr      = total_mrr      / count
    avg_ndcg     = total_ndcg     / count
    avg_coverage = total_coverage / count

    final_html = f"""
    <div style="padding:0;">
        {format_metric_html("Mean Reciprocal Rank (MRR)", avg_mrr, "mrr")}
        {format_metric_html("Normalized DCG (nDCG)", avg_ndcg, "ndcg")}
        {format_metric_html("Keyword Coverage", avg_coverage, "coverage", is_percentage=True)}
        <div style="margin-top:20px;padding:10px;background:#d4edda;border-radius:5px;text-align:center;border:1px solid #c3e6cb;">
            <span style="font-size:14px;color:#155724;font-weight:bold;">✓ Evaluation Complete: {count} tests</span>
        </div>
    </div>
    """

    df = pd.DataFrame([
        {"Category": cat, "Average MRR": sum(scores) / len(scores)}
        for cat, scores in category_mrr.items()
    ])
    return final_html, df


#  Answer 

def run_answer_evaluation(progress=gr.Progress()):
    total_accuracy = total_completeness = total_relevance = 0.0
    category_accuracy: dict[str, list[float]] = defaultdict(list)
    count = 0

    for test, result, prog_value in evaluate_all_answers():
        count += 1
        total_accuracy     += result.accuracy
        total_completeness += result.completeness
        total_relevance    += result.relevance
        category_accuracy[test.category].append(result.accuracy)
        progress(prog_value, desc=f"Evaluating test {count}...")

    avg_accuracy     = total_accuracy     / count
    avg_completeness = total_completeness / count
    avg_relevance    = total_relevance    / count

    final_html = f"""
    <div style="padding:0;">
        {format_metric_html("Accuracy",     avg_accuracy,     "accuracy",     score_format=True)}
        {format_metric_html("Completeness", avg_completeness, "completeness", score_format=True)}
        {format_metric_html("Relevance",    avg_relevance,    "relevance",    score_format=True)}
        <div style="margin-top:20px;padding:10px;background:#d4edda;border-radius:5px;text-align:center;border:1px solid #c3e6cb;">
            <span style="font-size:14px;color:#155724;font-weight:bold;">✓ Evaluation Complete: {count} tests</span>
        </div>
    </div>
    """

    df = pd.DataFrame([
        {"Category": cat, "Average Accuracy": sum(scores) / len(scores)}
        for cat, scores in category_accuracy.items()
    ])
    return final_html, df


#  App

def main():
    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    with gr.Blocks(title="Naheem's Personal Knowledge Assistant Evaluation Dashboard", theme=theme) as app:
        gr.Markdown("# 📊 Naheem's RAG Evaluation Dashboard")
        gr.Markdown("Naheem's Personal Knowledge Assistant Evaluation Dashboard")

        # Retrieval
        gr.Markdown("## 🔍 Retrieval Evaluation")
        retrieval_button = gr.Button("Run Evaluation", variant="primary", size="lg")
        with gr.Row():
            with gr.Column(scale=1):
                retrieval_metrics = gr.HTML(
                    "<div style='padding:20px;text-align:center;color:#999;'>Click 'Run Evaluation' to start</div>"
                )
            with gr.Column(scale=1):
                retrieval_chart = gr.BarPlot(
                    x="Category", y="Average MRR",
                    title="Average MRR by Category",
                    y_lim=[0, 1], height=400,
                )

        # Answer
        gr.Markdown("## 💬 Answer Evaluation")
        answer_button = gr.Button("Run Evaluation", variant="primary", size="lg")
        with gr.Row():
            with gr.Column(scale=1):
                answer_metrics = gr.HTML(
                    "<div style='padding:20px;text-align:center;color:#999;'>Click 'Run Evaluation' to start</div>"
                )
            with gr.Column(scale=1):
                answer_chart = gr.BarPlot(
                    x="Category", y="Average Accuracy",
                    title="Average Accuracy by Category",
                    y_lim=[1, 5], height=400,
                )

        retrieval_button.click(fn=run_retrieval_evaluation, outputs=[retrieval_metrics, retrieval_chart])
        answer_button.click(fn=run_answer_evaluation,       outputs=[answer_metrics,    answer_chart])

    app.launch(inbrowser=True)


if __name__ == "__main__":
    main()