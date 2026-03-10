"""
Evaluation dashboard for the pro implementation using eval3.
"""

import gradio as gr
import pandas as pd
import ast
from collections import defaultdict
from pathlib import Path
from dotenv import load_dotenv

from evaluation.eval3 import (
    evaluate_all_retrieval,
    evaluate_all_answers,
    GENERATION_MODEL,
    JUDGE_MODEL,
)
from evaluation.test3 import TEST_FILE
from pro_implementation.asnwer3 import (
    embedding_model as ANSWER_EMBEDDING_MODEL,
    RETRIEVAL_K,
    FINAL_K,
    MODEL as ANSWER_MODEL,
    collection_name as ANSWER_COLLECTION_NAME,
)

load_dotenv(override=True)
DEBUG = True


def dbg(message):
    if DEBUG:
        print(f"[EVALUATOR3] {message}")


def read_ingest_constants() -> dict:
    ingest_path = Path(__file__).parent / "pro_implementation" / "ingest3.py"
    wanted = {
        "MODEL",
        "embedding_model",
        "collection_name",
        "AVERAGE_CHUNK_SIZE",
        "DB_NAME",
        "KNOWLEDGE_BASE_PATH",
        "WORKERS",
    }
    values = {name: "N/A" for name in wanted}
    try:
        source = ingest_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in wanted:
                        try:
                            values[target.id] = ast.literal_eval(node.value)
                        except Exception:
                            values[target.id] = "non-literal"
    except Exception as exc:
        dbg(f"Could not read ingest3 constants: {exc}")
    if values.get("DB_NAME") == "non-literal":
        values["DB_NAME"] = str(Path(__file__).parent / "preprocessed_db")
    if values.get("KNOWLEDGE_BASE_PATH") == "non-literal":
        values["KNOWLEDGE_BASE_PATH"] = str(Path(__file__).parent / "knowledge-base")
    return values


def build_config_markdown() -> str:
    ingest_cfg = read_ingest_constants()
    retriever_backend = "Chroma"
    return f"""
### Current Configuration
- **Vector Backend:** `{retriever_backend}`
- **Answer Model (asnwer3, for rewrite/rerank/final answer):** `{ANSWER_MODEL}`
- **Retrieval top_k (asnwer3):** `{RETRIEVAL_K}`
- **Final context size final_k (asnwer3):** `{FINAL_K}`
- **Retriever collection (asnwer3):** `{ANSWER_COLLECTION_NAME}`
- **Embedding Model (asnwer3, for query embedding):** `{ANSWER_EMBEDDING_MODEL}`
- **Ingest Model (ingest3, for document chunking):** `{ingest_cfg.get('MODEL', 'N/A')}`
- **Embedding Model (ingest3, for document vectors):** `{ingest_cfg.get('embedding_model', 'N/A')}`
- **Ingest collection (ingest3):** `{ingest_cfg.get('collection_name', 'N/A')}`
- **Average Chunk Size (ingest3):** `{ingest_cfg.get('AVERAGE_CHUNK_SIZE', 'N/A')}`
- **Workers (ingest3):** `{ingest_cfg.get('WORKERS', 'N/A')}`
- **DB Name (ingest3):** `{ingest_cfg.get('DB_NAME', 'N/A')}`
- **Knowledge Base Path (ingest3):** `{ingest_cfg.get('KNOWLEDGE_BASE_PATH', 'N/A')}`
- **Generation Model (eval3, answers test questions):** `{GENERATION_MODEL}`
- **Judge Model (eval3, scores answer quality):** `{JUDGE_MODEL}`
- **Evaluation Test File:** `{TEST_FILE}`
"""


MRR_GREEN = 0.9
MRR_AMBER = 0.75
NDCG_GREEN = 0.9
NDCG_AMBER = 0.75
COVERAGE_GREEN = 90.0
COVERAGE_AMBER = 75.0

ANSWER_GREEN = 4.5
ANSWER_AMBER = 4.0


def get_color(value: float, metric_type: str) -> str:
    """Get color based on metric value and type."""
    if metric_type == "mrr":
        if value >= MRR_GREEN:
            return "green"
        elif value >= MRR_AMBER:
            return "orange"
        else:
            return "red"
    elif metric_type == "ndcg":
        if value >= NDCG_GREEN:
            return "green"
        elif value >= NDCG_AMBER:
            return "orange"
        else:
            return "red"
    elif metric_type == "coverage":
        if value >= COVERAGE_GREEN:
            return "green"
        elif value >= COVERAGE_AMBER:
            return "orange"
        else:
            return "red"
    elif metric_type in ["accuracy", "completeness", "relevance"]:
        if value >= ANSWER_GREEN:
            return "green"
        elif value >= ANSWER_AMBER:
            return "orange"
        else:
            return "red"
    return "black"


def format_metric_html(
    label: str,
    value: float,
    metric_type: str,
    is_percentage: bool = False,
    score_format: bool = False,
) -> str:
    """Format a metric with color coding."""
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


def run_retrieval_evaluation(progress=gr.Progress()):
    """Run retrieval evaluation and return final metrics plus chart data."""
    dbg("Starting retrieval evaluation run")
    total_mrr = 0.0
    total_ndcg = 0.0
    total_coverage = 0.0
    category_mrr = defaultdict(list)
    count = 0

    for test, result, prog_value in evaluate_all_retrieval():
        count += 1
        total_mrr += result.mrr
        total_ndcg += result.ndcg
        total_coverage += result.keyword_coverage
        category_mrr[test.category].append(result.mrr)
        progress(prog_value, desc=f"Evaluating test {count}...")
        dbg(f"Retrieval test {count}: category={test.category}, mrr={result.mrr:.4f}")

    avg_mrr = total_mrr / count if count > 0 else 0.0
    avg_ndcg = total_ndcg / count if count > 0 else 0.0
    avg_coverage = total_coverage / count if count > 0 else 0.0
    dbg(
        f"Retrieval averages -> MRR={avg_mrr:.4f}, nDCG={avg_ndcg:.4f}, coverage={avg_coverage:.1f}%"
    )

    final_html = f"""
    <div style="padding: 0;">
        {format_metric_html("Mean Reciprocal Rank (MRR)", avg_mrr, "mrr")}
        {format_metric_html("Normalized DCG (nDCG)", avg_ndcg, "ndcg")}
        {format_metric_html("Keyword Coverage", avg_coverage, "coverage", is_percentage=True)}
        <div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border-radius: 5px; text-align: center; border: 1px solid #c3e6cb;">
            <span style="font-size: 14px; color: #155724; font-weight: bold;">Evaluation Complete: {count} tests</span>
        </div>
    </div>
    """

    category_data = []
    for category, mrr_scores in category_mrr.items():
        avg_cat_mrr = sum(mrr_scores) / len(mrr_scores)
        category_data.append({"Category": category, "Average MRR": avg_cat_mrr})
    df = pd.DataFrame(category_data)
    dbg(f"Retrieval chart rows: {len(df)}")
    return final_html, df


def run_answer_evaluation(progress=gr.Progress()):
    """Run answer evaluation and return final metrics plus chart data."""
    dbg("Starting answer evaluation run")
    total_accuracy = 0.0
    total_completeness = 0.0
    total_relevance = 0.0
    category_accuracy = defaultdict(list)
    count = 0

    for test, result, prog_value in evaluate_all_answers():
        count += 1
        total_accuracy += result.accuracy
        total_completeness += result.completeness
        total_relevance += result.relevance
        category_accuracy[test.category].append(result.accuracy)
        progress(prog_value, desc=f"Evaluating test {count}...")
        dbg(f"Answer test {count}: category={test.category}, accuracy={result.accuracy:.2f}")

    avg_accuracy = total_accuracy / count if count > 0 else 0.0
    avg_completeness = total_completeness / count if count > 0 else 0.0
    avg_relevance = total_relevance / count if count > 0 else 0.0
    dbg(
        f"Answer averages -> accuracy={avg_accuracy:.2f}, completeness={avg_completeness:.2f}, relevance={avg_relevance:.2f}"
    )

    final_html = f"""
    <div style="padding: 0;">
        {format_metric_html("Accuracy", avg_accuracy, "accuracy", score_format=True)}
        {format_metric_html("Completeness", avg_completeness, "completeness", score_format=True)}
        {format_metric_html("Relevance", avg_relevance, "relevance", score_format=True)}
        <div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border-radius: 5px; text-align: center; border: 1px solid #c3e6cb;">
            <span style="font-size: 14px; color: #155724; font-weight: bold;">Evaluation Complete: {count} tests</span>
        </div>
    </div>
    """

    category_data = []
    for category, accuracy_scores in category_accuracy.items():
        avg_cat_accuracy = sum(accuracy_scores) / len(accuracy_scores)
        category_data.append({"Category": category, "Average Accuracy": avg_cat_accuracy})
    df = pd.DataFrame(category_data)
    dbg(f"Answer chart rows: {len(df)}")
    return final_html, df


def main():
    """Launch the Gradio evaluation app."""
    dbg("Building evaluator dashboard UI")
    dbg(f"Generation model (from eval3): {GENERATION_MODEL}")
    dbg(f"Judge model (from eval3): {JUDGE_MODEL}")
    dbg(f"Retrieval top_k (from asnwer3): {RETRIEVAL_K}")
    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])

    with gr.Blocks(title="RAG Evaluation Dashboard", theme=theme) as app:
        gr.Markdown("# RAG Evaluation Dashboard")
        gr.Markdown("Evaluate retrieval and answer quality for the Insurellm RAG system")
        gr.Markdown(build_config_markdown())

        gr.Markdown("## Retrieval Evaluation")
        retrieval_button = gr.Button("Run Evaluation", variant="primary", size="lg")

        with gr.Row():
            with gr.Column(scale=1):
                retrieval_metrics = gr.HTML(
                    "<div style='padding: 20px; text-align: center; color: #999;'>Click 'Run Evaluation' to start</div>"
                )
            with gr.Column(scale=1):
                retrieval_chart = gr.BarPlot(
                    x="Category",
                    y="Average MRR",
                    title="Average MRR by Category",
                    y_lim=[0, 1],
                    height=400,
                )

        gr.Markdown("## Answer Evaluation")
        answer_button = gr.Button("Run Evaluation", variant="primary", size="lg")

        with gr.Row():
            with gr.Column(scale=1):
                answer_metrics = gr.HTML(
                    "<div style='padding: 20px; text-align: center; color: #999;'>Click 'Run Evaluation' to start</div>"
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
    dbg("Evaluator dashboard launched")


if __name__ == "__main__":
    main()
