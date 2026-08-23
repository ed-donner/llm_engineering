"""Gradio UI for ARIA: agent-colored log stream and results table."""
import html
import logging
import queue
import sys
import os
import time

# Ensure chrys is on path
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

import gradio as gr
from dotenv import load_dotenv
load_dotenv()

from orchestrator import run_pipeline
from models import DecisionRecord

# Agent name + color for UI (logger name -> (display name, hex color))
AGENT_COLORS = {
    "aria.data_fetcher": ("DATA_FETCHER", "#3498db"),
    "aria.tech_analyst": ("TECH_ANALYST", "#27ae60"),
    "aria.sentiment_agent": ("SENTIMENT_AGENT", "#f39c12"),
    "aria.decision_agent": ("DECISION_AGENT", "#9b59b6"),
    "aria.notifier": ("NOTIFIER", "#1abc9c"),
}
DEFAULT_COLOR = "#bdc3c7"
MAX_LOG_LINES = 150


class AgentQueueHandler(logging.Handler):
    """Put (logger_name, formatted_message) into queue for colored UI."""
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self.log_queue.put((record.name, msg))
        except Exception:
            self.handleError(record)


def agent_line_to_html(logger_name: str, message: str) -> str:
    label, color = AGENT_COLORS.get(logger_name, ("ARIA", DEFAULT_COLOR))
    safe_msg = html.escape(message)
    return f'<span style="color:{color};font-weight:600">[{label}]</span> {safe_msg}'


def html_for_log(log_lines: list) -> str:
    recent = log_lines[-MAX_LOG_LINES:]
    content = "<br>".join(recent)
    return f"""
    <div style="height:420px;overflow-y:auto;border:1px solid #444;background:#1e1e2e;padding:12px;font-family:monospace;font-size:13px;color:#cdd6f4;">
    {content}
    </div>
    """


def setup_aria_logging(log_queue: queue.Queue) -> None:
    root = logging.getLogger()
    handler = AgentQueueHandler(log_queue)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    for name in AGENT_COLORS:
        logging.getLogger(name).setLevel(logging.INFO)


def table_for(records: list[DecisionRecord]) -> list[list]:
    if not records:
        return []
    return [
        [r.asset, str(r.tech_score), r.sentiment, f"{r.final_score:.1f}", r.decision, r.skip_reason or ""]
        for r in records
    ]


def run_pipeline_with_logging(log_queue: queue.Queue, result_queue: queue.Queue) -> None:
    try:
        records, _ = run_pipeline()
        result_queue.put(records)
    except Exception as e:
        logging.exception("Pipeline failed")
        result_queue.put([])


def run_clicked(log_state):
    log_queue = queue.Queue()
    result_queue = queue.Queue()
    root = logging.getLogger()
    for h in root.handlers[:]:
        if isinstance(h, AgentQueueHandler):
            root.removeHandler(h)
    setup_aria_logging(log_queue)
    log_lines = []
    thread = __import__("threading").Thread(
        target=run_pipeline_with_logging,
        args=(log_queue, result_queue),
        daemon=True,
    )
    thread.start()
    table = []
    while True:
        while True:
            try:
                logger_name, msg = log_queue.get_nowait()
                log_lines.append(agent_line_to_html(logger_name, msg))
            except queue.Empty:
                break
        try:
            records = result_queue.get_nowait()
            table = table_for(records)
            break
        except queue.Empty:
            pass
        yield log_lines, html_for_log(log_lines), table
        time.sleep(0.08)
        if not thread.is_alive():
            try:
                records = result_queue.get_nowait()
                table = table_for(records)
            except queue.Empty:
                table = []
            break
    yield log_lines, html_for_log(log_lines), table


def build_ui():
    with gr.Blocks(title="ARIA — Market Intelligence", theme=gr.themes.Soft(), css="""
        .log-panel { font-family: ui-monospace, monospace; }
    """) as ui:
        gr.Markdown("# ARIA — Automated Real-time Investment Alert Agent")
        gr.Markdown("Multi-agent pipeline: Data → Tech Analysis → Sentiment → Decision → Pushover alerts.")
        log_state = gr.State([])
        with gr.Row():
            run_btn = gr.Button("Run pipeline", variant="primary")
        with gr.Row():
            log_html = gr.HTML(value=html_for_log([]), label="Agent log")
        with gr.Row():
            results_df = gr.Dataframe(
                headers=["Asset", "Tech score", "Sentiment", "Final score", "Decision", "Skip reason"],
                datatype=["str", "str", "str", "str", "str", "str"],
                label="Last run results",
            )
        run_btn.click(
            fn=run_clicked,
            inputs=[log_state],
            outputs=[log_state, log_html, results_df],
        )
    return ui


if __name__ == "__main__":
    ui = build_ui()
    ui.launch(share=False, inbrowser=True)
