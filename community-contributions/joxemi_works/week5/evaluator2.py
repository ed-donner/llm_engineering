"""
ULTRA DUMMIE DESCRIPTION
------------------------
What this file does:
- Launches a Gradio dashboard to evaluate your RAG system.
- Runs two evaluation pipelines:
  1) Retrieval quality
  2) Answer quality
- Shows color-coded metrics and bar charts by category.

Internal steps:
1) Imports evaluation generators from evaluation.eval2.
2) Runs all tests and accumulates averages.
3) Builds HTML metric cards with traffic-light colors.
4) Builds chart dataframes for category-level comparison.
5) Launches a Gradio app with two buttons (retrieval / answer).

Key logic:
- This file is only UI orchestration.
- Core scoring logic lives in evaluation/eval2.py.
"""

import gradio as gr  # Imports Gradio to build the evaluation dashboard UI.
import pandas as pd  # Imports pandas to build chart dataframes.
import ast  # Imports AST parsing to read static constants from source files safely.
from collections import defaultdict  # Imports defaultdict for grouped metric aggregation.
from pathlib import Path  # Imports Path for robust filesystem path building.
from dotenv import load_dotenv  # Imports .env loader for runtime configuration.

from evaluation.eval2 import (  # Imports evaluation generators and model configuration from eval2 pipeline.
    evaluate_all_retrieval,
    evaluate_all_answers,
    GENERATION_MODEL,
    JUDGE_MODEL,
)
from evaluation.test2 import TEST_FILE  # Imports evaluation dataset path from test2 module.
from implementation.answer2 import (  # Imports runtime answer configuration used by retrieval/generation flow.
    EMBEDDING_MODEL as ANSWER_EMBEDDING_MODEL,
    RETRIEVAL_K,
)

load_dotenv(override=True)  # Loads environment variables and allows overwrite.
DEBUG = True  # Enables or disables debug traces in this module.


def dbg(message):  # Defines helper to print traces only when DEBUG is active.
    if DEBUG:  # Checks debug flag.
        print(f"[EVALUATOR] {message}")  # Prints debug line with module prefix.


def read_ingest_constants() -> dict:  # Defines helper to read ingest2 constants without importing heavy runtime objects.
    ingest_path = Path(__file__).parent / "implementation" / "ingest2.py"  # Resolves ingest2 path from current file directory.
    wanted = {"EMBEDDING_MODEL", "CHUNK_SIZE", "CHUNK_OVERLAP", "KNOWLEDGE_BASE", "DB_NAME"}  # Declares constant names to extract.
    values = {name: "N/A" for name in wanted}  # Initializes fallback values in case parsing fails.
    try:  # Starts safe parse block.
        source = ingest_path.read_text(encoding="utf-8")  # Reads ingest2 source file as text.
        tree = ast.parse(source)  # Parses source code into AST.
        for node in tree.body:  # Iterates top-level AST nodes.
            if isinstance(node, ast.Assign):  # Filters assignment statements.
                for target in node.targets:  # Iterates assignment targets.
                    if isinstance(target, ast.Name) and target.id in wanted:  # Selects wanted constant names.
                        try:  # Starts safe literal extraction block.
                            values[target.id] = ast.literal_eval(node.value)  # Extracts literal value from assignment.
                        except Exception:  # Handles non-literal expressions safely.
                            values[target.id] = "non-literal"  # Marks values computed dynamically.
    except Exception as exc:  # Handles file read/parse issues.
        dbg(f"Could not read ingest2 constants: {exc}")  # Traces parse failure reason.
    return values  # Returns extracted ingest constants map.


def build_config_markdown() -> str:  # Defines helper to generate UI markdown showing current configuration.
    ingest_cfg = read_ingest_constants()  # Reads ingestion-side constants from ingest2 source.
    retriever_backend = "Chroma"  # Declares active vector backend used by answer2/eval2 flow.
    return f"""  # Returns formatted markdown for UI display.
### Current Configuration
- **Vector Backend:** `{retriever_backend}`
- **Retrieval top_k (answer2):** `{RETRIEVAL_K}`
- **Embedding Model (answer2):** `{ANSWER_EMBEDDING_MODEL}`
- **Embedding Model (ingest2):** `{ingest_cfg.get('EMBEDDING_MODEL', 'N/A')}`
- **Chunk Size (ingest2):** `{ingest_cfg.get('CHUNK_SIZE', 'N/A')}`
- **Chunk Overlap (ingest2):** `{ingest_cfg.get('CHUNK_OVERLAP', 'N/A')}`
- **Generation Model (eval2):** `{GENERATION_MODEL}`
- **Judge Model (eval2):** `{JUDGE_MODEL}`
- **Evaluation Test File:** `{TEST_FILE}`
"""  # Closes configuration markdown block.


# Color coding thresholds - Retrieval  # Declares threshold section for retrieval metric colors.
MRR_GREEN = 0.9  # Defines green threshold for MRR.
MRR_AMBER = 0.75  # Defines amber threshold for MRR.
NDCG_GREEN = 0.9  # Defines green threshold for nDCG.
NDCG_AMBER = 0.75  # Defines amber threshold for nDCG.
COVERAGE_GREEN = 90.0  # Defines green threshold for keyword coverage percentage.
COVERAGE_AMBER = 75.0  # Defines amber threshold for keyword coverage percentage.

# Color coding thresholds - Answer (1-5 scale)  # Declares threshold section for answer metric colors.
ANSWER_GREEN = 4.5  # Defines green threshold for answer metrics.
ANSWER_AMBER = 4.0  # Defines amber threshold for answer metrics.


def get_color(value: float, metric_type: str) -> str:  # Defines color selector for metric values.
    """Get color based on metric value and type."""  # Documents color selection behavior.
    if metric_type == "mrr":  # Checks MRR metric.
        if value >= MRR_GREEN:  # Applies green threshold.
            return "green"  # Returns green color.
        elif value >= MRR_AMBER:  # Applies amber threshold.
            return "orange"  # Returns orange color.
        else:  # Handles low values.
            return "red"  # Returns red color.
    elif metric_type == "ndcg":  # Checks nDCG metric.
        if value >= NDCG_GREEN:  # Applies green threshold.
            return "green"  # Returns green color.
        elif value >= NDCG_AMBER:  # Applies amber threshold.
            return "orange"  # Returns orange color.
        else:  # Handles low values.
            return "red"  # Returns red color.
    elif metric_type == "coverage":  # Checks coverage metric.
        if value >= COVERAGE_GREEN:  # Applies green threshold.
            return "green"  # Returns green color.
        elif value >= COVERAGE_AMBER:  # Applies amber threshold.
            return "orange"  # Returns orange color.
        else:  # Handles low values.
            return "red"  # Returns red color.
    elif metric_type in ["accuracy", "completeness", "relevance"]:  # Checks answer-scoring metrics.
        if value >= ANSWER_GREEN:  # Applies green threshold.
            return "green"  # Returns green color.
        elif value >= ANSWER_AMBER:  # Applies amber threshold.
            return "orange"  # Returns orange color.
        else:  # Handles low values.
            return "red"  # Returns red color.
    return "black"  # Returns fallback color for unknown metric types.


def format_metric_html(  # Defines helper to build one styled metric card.
    label: str,  # Receives metric label text.
    value: float,  # Receives numeric metric value.
    metric_type: str,  # Receives metric type key for color mapping.
    is_percentage: bool = False,  # Receives flag to show value as percentage.
    score_format: bool = False,  # Receives flag to show value as x.xx/5 score.
) -> str:  # Returns HTML string for one metric card.
    """Format a metric with color coding."""  # Documents metric-card formatting behavior.
    color = get_color(value, metric_type)  # Computes card color from metric value and type.
    if is_percentage:  # Checks if percentage formatting is required.
        value_str = f"{value:.1f}%"  # Formats value as percentage.
    elif score_format:  # Checks if score formatting is required.
        value_str = f"{value:.2f}/5"  # Formats value as score out of 5.
    else:  # Handles default numeric format.
        value_str = f"{value:.4f}"  # Formats value with four decimals.
    return f"""
    <div style="margin: 10px 0; padding: 15px; background-color: #f5f5f5; border-radius: 8px; border-left: 5px solid {color};">
        <div style="font-size: 14px; color: #666; margin-bottom: 5px;">{label}</div>
        <div style="font-size: 28px; font-weight: bold; color: {color};">{value_str}</div>
    </div>
    """  # Returns full metric card HTML.


def run_retrieval_evaluation(progress=gr.Progress()):  # Defines retrieval dashboard pipeline callback.
    """Run retrieval evaluation and return final metrics plus chart data."""  # Documents retrieval evaluation callback.
    dbg("Starting retrieval evaluation run")  # Traces retrieval run start.
    total_mrr = 0.0  # Initializes sum accumulator for MRR.
    total_ndcg = 0.0  # Initializes sum accumulator for nDCG.
    total_coverage = 0.0  # Initializes sum accumulator for keyword coverage.
    category_mrr = defaultdict(list)  # Initializes grouped storage for category MRR values.
    count = 0  # Initializes processed test counter.

    for test, result, prog_value in evaluate_all_retrieval():  # Iterates through retrieval results from eval2 generator.
        count += 1  # Increments test counter.
        total_mrr += result.mrr  # Adds current test MRR to sum.
        total_ndcg += result.ndcg  # Adds current test nDCG to sum.
        total_coverage += result.keyword_coverage  # Adds current test coverage to sum.
        category_mrr[test.category].append(result.mrr)  # Stores MRR under test category for chart aggregation.
        progress(prog_value, desc=f"Evaluating test {count}...")  # Updates Gradio progress bar.
        dbg(f"Retrieval test {count}: category={test.category}, mrr={result.mrr:.4f}")  # Traces per-test retrieval snapshot.

    avg_mrr = total_mrr / count if count > 0 else 0.0  # Computes average MRR safely.
    avg_ndcg = total_ndcg / count if count > 0 else 0.0  # Computes average nDCG safely.
    avg_coverage = total_coverage / count if count > 0 else 0.0  # Computes average coverage safely.
    dbg(f"Retrieval averages -> MRR={avg_mrr:.4f}, nDCG={avg_ndcg:.4f}, coverage={avg_coverage:.1f}%")  # Traces final retrieval averages.

    final_html = f"""
    <div style="padding: 0;">
        {format_metric_html("Mean Reciprocal Rank (MRR)", avg_mrr, "mrr")}
        {format_metric_html("Normalized DCG (nDCG)", avg_ndcg, "ndcg")}
        {format_metric_html("Keyword Coverage", avg_coverage, "coverage", is_percentage=True)}
        <div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border-radius: 5px; text-align: center; border: 1px solid #c3e6cb;">
            <span style="font-size: 14px; color: #155724; font-weight: bold;">Evaluation Complete: {count} tests</span>
        </div>
    </div>
    """  # Builds final retrieval summary cards HTML.

    category_data = []  # Initializes row list for retrieval category bar chart.
    for category, mrr_scores in category_mrr.items():  # Iterates grouped MRR scores per category.
        avg_cat_mrr = sum(mrr_scores) / len(mrr_scores)  # Computes category average MRR.
        category_data.append({"Category": category, "Average MRR": avg_cat_mrr})  # Appends one chart row.
    df = pd.DataFrame(category_data)  # Builds dataframe for retrieval bar chart component.
    dbg(f"Retrieval chart rows: {len(df)}")  # Traces chart row count.
    return final_html, df  # Returns summary HTML and chart dataframe.


def run_answer_evaluation(progress=gr.Progress()):  # Defines answer dashboard pipeline callback.
    """Run answer evaluation and return final metrics plus chart data."""  # Documents answer evaluation callback.
    dbg("Starting answer evaluation run")  # Traces answer run start.
    total_accuracy = 0.0  # Initializes sum accumulator for accuracy.
    total_completeness = 0.0  # Initializes sum accumulator for completeness.
    total_relevance = 0.0  # Initializes sum accumulator for relevance.
    category_accuracy = defaultdict(list)  # Initializes grouped storage for category accuracy values.
    count = 0  # Initializes processed test counter.

    for test, result, prog_value in evaluate_all_answers():  # Iterates through answer results from eval2 generator.
        count += 1  # Increments test counter.
        total_accuracy += result.accuracy  # Adds current test accuracy to sum.
        total_completeness += result.completeness  # Adds current test completeness to sum.
        total_relevance += result.relevance  # Adds current test relevance to sum.
        category_accuracy[test.category].append(result.accuracy)  # Stores accuracy under test category for chart aggregation.
        progress(prog_value, desc=f"Evaluating test {count}...")  # Updates Gradio progress bar.
        dbg(f"Answer test {count}: category={test.category}, accuracy={result.accuracy:.2f}")  # Traces per-test answer snapshot.

    avg_accuracy = total_accuracy / count if count > 0 else 0.0  # Computes average accuracy safely.
    avg_completeness = total_completeness / count if count > 0 else 0.0  # Computes average completeness safely.
    avg_relevance = total_relevance / count if count > 0 else 0.0  # Computes average relevance safely.
    dbg(  # Traces final answer averages.
        f"Answer averages -> accuracy={avg_accuracy:.2f}, completeness={avg_completeness:.2f}, relevance={avg_relevance:.2f}"
    )  # Closes debug line.

    final_html = f"""
    <div style="padding: 0;">
        {format_metric_html("Accuracy", avg_accuracy, "accuracy", score_format=True)}
        {format_metric_html("Completeness", avg_completeness, "completeness", score_format=True)}
        {format_metric_html("Relevance", avg_relevance, "relevance", score_format=True)}
        <div style="margin-top: 20px; padding: 10px; background-color: #d4edda; border-radius: 5px; text-align: center; border: 1px solid #c3e6cb;">
            <span style="font-size: 14px; color: #155724; font-weight: bold;">Evaluation Complete: {count} tests</span>
        </div>
    </div>
    """  # Builds final answer summary cards HTML.

    category_data = []  # Initializes row list for answer category bar chart.
    for category, accuracy_scores in category_accuracy.items():  # Iterates grouped accuracy scores per category.
        avg_cat_accuracy = sum(accuracy_scores) / len(accuracy_scores)  # Computes category average accuracy.
        category_data.append({"Category": category, "Average Accuracy": avg_cat_accuracy})  # Appends one chart row.
    df = pd.DataFrame(category_data)  # Builds dataframe for answer bar chart component.
    dbg(f"Answer chart rows: {len(df)}")  # Traces chart row count.
    return final_html, df  # Returns summary HTML and chart dataframe.


def main():  # Defines main function to build and launch the Gradio dashboard.
    """Launch the Gradio evaluation app."""  # Documents dashboard entrypoint behavior.
    dbg("Building evaluator dashboard UI")  # Traces UI build start.
    dbg(f"Generation model (from eval2): {GENERATION_MODEL}")  # Traces generation model read from eval2 config.
    dbg(f"Judge model (from eval2): {JUDGE_MODEL}")  # Traces judge model read from eval2 config.
    dbg(f"Retrieval top_k (from answer2): {RETRIEVAL_K}")  # Traces retrieval depth configured in answer2.
    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])  # Configures dashboard theme.

    with gr.Blocks(title="RAG Evaluation Dashboard", theme=theme) as app:  # Creates main dashboard container.
        gr.Markdown("# RAG Evaluation Dashboard")  # Renders dashboard title.
        gr.Markdown("Evaluate retrieval and answer quality for the Insurellm RAG system")  # Renders dashboard subtitle.
        gr.Markdown(build_config_markdown())  # Renders full runtime configuration block used by evaluator2 pipeline.

        gr.Markdown("## Retrieval Evaluation")  # Renders retrieval section heading.
        retrieval_button = gr.Button("Run Evaluation", variant="primary", size="lg")  # Creates retrieval evaluation button.

        with gr.Row():  # Creates row for retrieval outputs.
            with gr.Column(scale=1):  # Creates left column for retrieval metric cards.
                retrieval_metrics = gr.HTML(  # Creates HTML component for retrieval summary cards.
                    "<div style='padding: 20px; text-align: center; color: #999;'>Click 'Run Evaluation' to start</div>"
                )  # Closes retrieval HTML component.
            with gr.Column(scale=1):  # Creates right column for retrieval category chart.
                retrieval_chart = gr.BarPlot(  # Creates retrieval bar chart component.
                    x="Category",  # Sets x-axis column name.
                    y="Average MRR",  # Sets y-axis column name.
                    title="Average MRR by Category",  # Sets chart title.
                    y_lim=[0, 1],  # Sets retrieval metric axis limits.
                    height=400,  # Sets chart height.
                )  # Closes retrieval chart component.

        gr.Markdown("## Answer Evaluation")  # Renders answer section heading.
        answer_button = gr.Button("Run Evaluation", variant="primary", size="lg")  # Creates answer evaluation button.

        with gr.Row():  # Creates row for answer outputs.
            with gr.Column(scale=1):  # Creates left column for answer metric cards.
                answer_metrics = gr.HTML(  # Creates HTML component for answer summary cards.
                    "<div style='padding: 20px; text-align: center; color: #999;'>Click 'Run Evaluation' to start</div>"
                )  # Closes answer HTML component.
            with gr.Column(scale=1):  # Creates right column for answer category chart.
                answer_chart = gr.BarPlot(  # Creates answer bar chart component.
                    x="Category",  # Sets x-axis column name.
                    y="Average Accuracy",  # Sets y-axis column name.
                    title="Average Accuracy by Category",  # Sets chart title.
                    y_lim=[1, 5],  # Sets answer metric axis limits.
                    height=400,  # Sets chart height.
                )  # Closes answer chart component.

        retrieval_button.click(  # Wires retrieval button click event.
            fn=run_retrieval_evaluation,  # Sets retrieval evaluation callback.
            outputs=[retrieval_metrics, retrieval_chart],  # Sets retrieval output components.
        )  # Closes retrieval click binding.
        answer_button.click(  # Wires answer button click event.
            fn=run_answer_evaluation,  # Sets answer evaluation callback.
            outputs=[answer_metrics, answer_chart],  # Sets answer output components.
        )  # Closes answer click binding.

    app.launch(inbrowser=True)  # Starts Gradio app and opens browser automatically.
    dbg("Evaluator dashboard launched")  # Traces successful dashboard launch.


if __name__ == "__main__":  # Runs main only when file is executed directly.
    main()  # Launches dashboard entrypoint.
