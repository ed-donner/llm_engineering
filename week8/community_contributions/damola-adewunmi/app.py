"""
Deal Hunter — Gradio UI for the multi-agent PlayStation UK gift card pipeline.
Run from this directory: uv run app.py (or python app.py with deps installed).
"""

import os
import sys

# Ensure project root is on path when run from repo root or week8
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from dotenv import load_dotenv
load_dotenv()

import gradio as gr

from graph import run_deal_hunter

TABLE_HEADERS = [
    "Retailer",
    "Denomination (£)",
    "Price (£)",
    "Discount %",
    "Verdict",
    "URL",
]


def run_pipeline(query: str) -> tuple[list[list[str]], str]:
    """Run Searcher → Valuer → Strategist and return table rows + message."""
    if not query.strip():
        query = "PlayStation UK gift card price CDKeys ShopTo Eneba GAME"
    result = run_deal_hunter(search_query=query)
    table = result.get("summary_table") or []
    message = result.get("summary_message") or "Done."
    return table, message


def build_ui():
    with gr.Blocks(title="Deal Hunter — PlayStation UK", theme=gr.themes.Soft()) as ui:
        gr.Markdown(
            "# 🎮 Deal Hunter — PlayStation UK Gift Cards\n"
            "Multi-agent pipeline: **Searcher** (Tavily) → **Valuer** (GPT-4o specialist) → **Strategist** (summary table).  \n"
            "Rule: *Strong Buy* = discount >12%; typical retail is 5–10%."
        )
        with gr.Row():
            search_input = gr.Textbox(
                label="Search query (optional)",
                placeholder="e.g. PlayStation UK gift card CDKeys ShopTo",
                value="PlayStation UK gift card price CDKeys ShopTo Eneba GAME",
            )
            run_btn = gr.Button("Run pipeline", variant="primary")
        summary_msg = gr.Markdown(value="Run the pipeline to see results.")
        table_out = gr.Dataframe(
            headers=TABLE_HEADERS,
            label="Deals",
            wrap=True,
            column_widths=["1", "1", "1", "1", "1", "2"],
            row_count=15,
            col_count=6,
            max_height=450,
        )

        def on_run(q: str):
            rows, msg = run_pipeline(q)
            return rows, msg

        run_btn.click(
            fn=on_run,
            inputs=[search_input],
            outputs=[table_out, summary_msg],
        )

        # Pre-fill empty table so headers show
        ui.load(
            fn=lambda: ([], "Enter a query and click **Run pipeline** (uses Tavily + GPT-4o)."),
            inputs=[],
            outputs=[table_out, summary_msg],
        )
    return ui


if __name__ == "__main__":
    app = build_ui()
    app.launch(inbrowser=True)
