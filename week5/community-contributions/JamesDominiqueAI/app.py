# app.py
"""
app.py — Gradio UI for Regulatory Compliance RAG.

Two tabs:
  1. 💬 Chat — Ask questions, see answers + retrieved context side by side
  2. 📊 Evaluation — Run retrieval (MRR/nDCG) and answer (LLM-as-judge) evals with charts

Run:
    python app.py
    python app.py --ingest         # Build the index first
    python app.py --force-reingest # Rebuild from scratch
    python app.py --eval           # CLI-only eval (no UI)
"""

import argparse
import sys
import os
import pandas as pd
import gradio as gr
from dotenv import load_dotenv

load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import MODEL


# ── Helper ─────────────────────────────────────────────────────────────────────

def format_context(chunks) -> str:
    """Format retrieved chunks for the context panel."""
    result = "<h2 style='color: #ff7800;'>📚 Retrieved Context</h2>\n\n"
    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        doc_type = chunk.metadata.get("type", "")
        result += f"<span style='color: #ff7800; font-weight:bold;'>Source: {source} ({doc_type})</span>\n\n"
        result += chunk.page_content[:600] + ("..." if len(chunk.page_content) > 600 else "")
        result += "\n\n---\n\n"
    return result


# ── Chat Tab ───────────────────────────────────────────────────────────────────

def _extract_text(content) -> str:
    """Extract plain string from Gradio 6 message content (may be string or list of blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(block.get("text", "") for block in content if isinstance(block, dict))
    return str(content)


def chat(history):
    """Process the latest message and return updated history + context."""
    try:
        from rag.answer import answer_question
        last_message = _extract_text(history[-1]["content"])
        prior = [
            {"role": m["role"], "content": _extract_text(m["content"])}
            for m in history[:-1]
        ]
        print(f"[Chat] Answering: {last_message}")
        answer, chunks = answer_question(last_message, prior)
        print(f"[Chat] Answer ready ({len(answer)} chars)")
        history.append({"role": "assistant", "content": answer})
        return history, format_context(chunks)
    except Exception as e:
        import traceback
        error_msg = f"❌ Error: {str(e)}\n\n```\n{traceback.format_exc()}\n```"
        print(f"[Chat] ERROR: {traceback.format_exc()}")
        history.append({"role": "assistant", "content": error_msg})
        return history, f"<pre>{traceback.format_exc()}</pre>"


def put_message_in_chatbot(message, history):
    history = history + [{"role": "user", "content": message}]
    return "", history


# ── Evaluation Tab ─────────────────────────────────────────────────────────────

# Color thresholds
MRR_GREEN, MRR_AMBER = 0.9, 0.75
NDCG_GREEN, NDCG_AMBER = 0.9, 0.75
COVERAGE_GREEN, COVERAGE_AMBER = 90.0, 75.0
ANSWER_GREEN, ANSWER_AMBER = 4.5, 4.0


def _get_color(value: float, kind: str) -> str:
    thresholds = {
        "mrr": (MRR_GREEN, MRR_AMBER),
        "ndcg": (NDCG_GREEN, NDCG_AMBER),
        "coverage": (COVERAGE_GREEN, COVERAGE_AMBER),
        "answer": (ANSWER_GREEN, ANSWER_AMBER),
    }
    g, a = thresholds.get(kind, (0.9, 0.75))
    return "green" if value >= g else ("orange" if value >= a else "red")


def _metric_card(label: str, value: float, kind: str, fmt: str = ".4f") -> str:
    color = _get_color(value, kind)
    formatted = f"{value:{fmt}}"
    return f"""
    <div style="margin:10px 0;padding:15px;background:#f5f5f5;border-radius:8px;border-left:5px solid {color};">
        <div style="font-size:14px;color:#666;margin-bottom:5px;">{label}</div>
        <div style="font-size:28px;font-weight:bold;color:{color};">{formatted}</div>
    </div>"""


def _make_bar_chart(df, x_col: str, y_col: str, title: str, y_max: float):
    """Create a matplotlib bar chart compatible with gr.Plot."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4))
    if df is not None and not df.empty:
        ax.bar(df[x_col], df[y_col], color="#ff7800", edgecolor="white")
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_ylim(0, y_max)
        ax.tick_params(axis="x", rotation=20)
    else:
        ax.text(0.5, 0.5, "No data yet", ha="center", va="center", transform=ax.transAxes)
    plt.tight_layout()
    return fig


def run_retrieval_evaluation(progress=gr.Progress()):
    from evaluation.retrieval_eval import evaluate_all_retrieval, load_tests
    from collections import defaultdict
    total_tests = len(load_tests())
    total_mrr = total_ndcg = total_cov = 0.0
    category_mrr = defaultdict(list)
    count = 0

    for test, result, prog in evaluate_all_retrieval():
        count += 1
        total_mrr += result.mrr
        total_ndcg += result.ndcg
        total_cov += result.keyword_coverage
        category_mrr[test.category].append(result.mrr)
        progress(prog, desc=f"Evaluating test {count} of {total_tests}...")

    avg_mrr = total_mrr / count
    avg_ndcg = total_ndcg / count
    avg_cov = total_cov / count

    html = f"""<div style="padding:0;">
        {_metric_card("Mean Reciprocal Rank (MRR)", avg_mrr, "mrr")}
        {_metric_card("Normalized DCG (nDCG)", avg_ndcg, "ndcg")}
        {_metric_card("Keyword Coverage", avg_cov, "coverage", fmt=".1f")}
        <div style="margin-top:20px;padding:10px;background:#d4edda;border-radius:5px;text-align:center;border:1px solid #c3e6cb;">
            <span style="font-size:14px;color:#155724;font-weight:bold;">✓ Complete: {total_tests} tests</span>
        </div>
    </div>"""

    df = pd.DataFrame([
        {"Category": cat, "Average MRR": round(sum(s) / len(s), 3)}
        for cat, s in category_mrr.items()
    ])
    fig = _make_bar_chart(df, "Category", "Average MRR", "Average MRR by Category", 1.0)
    return html, fig


def run_answer_evaluation(progress=gr.Progress()):
    from evaluation.answer_eval import evaluate_all_answers
    from evaluation.retrieval_eval import load_tests
    from collections import defaultdict
    total_tests = len(load_tests())
    total_acc = total_comp = total_rel = 0.0
    category_acc = defaultdict(list)
    count = 0

    for test, result, prog in evaluate_all_answers():
        count += 1
        total_acc += result.accuracy
        total_comp += result.completeness
        total_rel += result.relevance
        category_acc[test.category].append(result.accuracy)
        progress(prog, desc=f"Evaluating test {count} of {total_tests}...")

    avg_acc = total_acc / count
    avg_comp = total_comp / count
    avg_rel = total_rel / count

    html = f"""<div style="padding:0;">
        {_metric_card("Accuracy", avg_acc, "answer", fmt=".2f")}
        {_metric_card("Completeness", avg_comp, "answer", fmt=".2f")}
        {_metric_card("Relevance", avg_rel, "answer", fmt=".2f")}
        <div style="margin-top:20px;padding:10px;background:#d4edda;border-radius:5px;text-align:center;border:1px solid #c3e6cb;">
            <span style="font-size:14px;color:#155724;font-weight:bold;">✓ Complete: {total_tests} tests</span>
        </div>
    </div>"""

    df = pd.DataFrame([
        {"Category": cat, "Average Accuracy": round(sum(s) / len(s), 2)}
        for cat, s in category_acc.items()
    ])
    fig = _make_bar_chart(df, "Category", "Average Accuracy", "Average Accuracy by Category", 5.0)
    return html, fig


# ── Main UI ────────────────────────────────────────────────────────────────────

def main():
    with gr.Blocks(title="Regulatory Compliance RAG") as ui:
        gr.Markdown(f"# 🏛️ Regulatory Compliance RAG\nPowered by `{MODEL}` · Ask questions about financial regulations")

        with gr.Tabs():

            # ── Chat Tab ───────────────────────────────────────────────────────
            with gr.TabItem("💬 Chat"):
                with gr.Row():
                    with gr.Column(scale=1):
                        chatbot = gr.Chatbot(
                            label="Conversation",
                            height=600,
                        )
                        message = gr.Textbox(
                            placeholder="Ask anything about the regulations...",
                            show_label=False,
                        )

                    with gr.Column(scale=1):
                        context_panel = gr.Markdown(
                            value="*Retrieved context will appear here after your first question.*",
                            label="Retrieved Context",
                            container=True,
                            height=600,
                        )

                message.submit(
                    put_message_in_chatbot,
                    inputs=[message, chatbot],
                    outputs=[message, chatbot],
                ).then(
                    chat,
                    inputs=[chatbot],
                    outputs=[chatbot, context_panel],
                )

            # ── Evaluation Tab ─────────────────────────────────────────────────
            with gr.TabItem("📊 Evaluation"):
                gr.Markdown("## 🔍 Retrieval Evaluation\nMeasures MRR and nDCG — how well the system finds the right chunks.")

                retrieval_btn = gr.Button("Run Retrieval Evaluation", variant="primary", size="lg")
                with gr.Row():
                    with gr.Column(scale=1):
                        retrieval_metrics = gr.HTML(
                            "<div style='padding:20px;text-align:center;color:#999;'>Click to start</div>"
                        )
                    with gr.Column(scale=1):
                        retrieval_chart = gr.Plot(label="MRR by Category")

                gr.Markdown("## 💬 Answer Evaluation\nLLM-as-judge scoring accuracy, completeness, and relevance (1–5 scale).")

                answer_btn = gr.Button("Run Answer Evaluation", variant="primary", size="lg")
                with gr.Row():
                    with gr.Column(scale=1):
                        answer_metrics = gr.HTML(
                            "<div style='padding:20px;text-align:center;color:#999;'>Click to start</div>"
                        )
                    with gr.Column(scale=1):
                        answer_chart = gr.Plot(label="Accuracy by Category")

                retrieval_btn.click(fn=run_retrieval_evaluation, outputs=[retrieval_metrics, retrieval_chart])
                answer_btn.click(fn=run_answer_evaluation, outputs=[answer_metrics, answer_chart])

    ui.launch(inbrowser=True, theme=gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"]))


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regulatory Compliance RAG")
    parser.add_argument("--ingest", action="store_true", help="Build the vector index")
    parser.add_argument("--force-reingest", action="store_true", help="Force rebuild index")
    parser.add_argument("--eval", action="store_true", help="Run retrieval eval (CLI)")
    parser.add_argument("--eval-answers", action="store_true", help="Run answer eval (CLI)")
    args = parser.parse_args()

    if args.ingest or args.force_reingest:
        from ingest.embedder import build_index
        build_index(force_reingest=args.force_reingest)

    elif args.eval:
        from evaluation.retrieval_eval import run_cli_eval
        run_cli_eval()

    elif args.eval_answers:
        from evaluation.answer_eval import run_cli_eval
        run_cli_eval()

    else:
        main()