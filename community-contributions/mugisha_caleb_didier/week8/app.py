"""
NewsHound - Autonomous Multi-Agent Tech News Intelligence System

A production-ready agentic AI system that monitors tech news feeds, analyzes
article importance using RAG + Modal ML scoring + frontier LLMs, and sends
push notifications for significant stories via Pushover.

Run: uv run community-contributions/mugisha_caleb_didier/week8/app.py
"""

import os
import logging
import queue
import threading
import time
import gradio as gr
from framework import NewsFramework, reformat
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

SCAN_INTERVAL = int(os.getenv("NEWSHOUND_INTERVAL", "300"))

HEADER_HTML = """
<div style="text-align:center; padding:10px 0 2px 0;">
    <h1 style="margin:0; font-size:30px; letter-spacing:1px; color:#e0e0e0;">
        <span style="color:#00dddd;">News</span>Hound
    </h1>
    <p style="color:#777; margin:4px 0 0; font-size:13px;">
        Autonomous multi-agent tech news intelligence system
    </p>
</div>
"""


def make_stats_html(stories, alerts, kb_size, last_scan=""):
    def card(value, label, color):
        return (
            '<div style="background:rgba(26,26,46,0.85); border-radius:8px; '
            'padding:14px 24px; text-align:center; min-width:110px; border:1px solid #333;">'
            f'<div style="color:{color}; font-size:26px; font-weight:bold;">{value}</div>'
            f'<div style="color:#777; font-size:11px; margin-top:2px;">{label}</div>'
            "</div>"
        )

    return (
        '<div style="display:flex; gap:12px; justify-content:center; margin:2px 0 6px 0;">'
        + card(stories, "Stories Found", "#00dddd")
        + card(alerts, "Alerts Sent", "#00dd00")
        + card(kb_size, "Knowledge Base", "#dddd00")
        + card(last_scan or "--:--", "Last Scan", "#ff7800")
        + "</div>"
    )


PIPELINE_HTML = """
<div style="background:rgba(26,26,46,0.85); border-radius:8px; padding:14px 16px;
            border:1px solid #333;">
    <div style="color:#e0e0e0; font-size:14px; font-weight:600; margin-bottom:10px;">
        Agent Pipeline
    </div>
    <table style="width:100%; font-size:12px; line-height:2.2;">
        <tr>
            <td style="color:#00dddd; font-weight:600; width:95px; padding-left:4px;">Scanner</td>
            <td style="color:#888;">RSS feeds + Structured Outputs (Pydantic)</td>
        </tr>
        <tr>
            <td style="color:#4488ff; font-weight:600; padding-left:4px;">Knowledge</td>
            <td style="color:#888;">ChromaDB RAG + SentenceTransformer</td>
        </tr>
        <tr>
            <td style="color:#dddd00; font-weight:600; padding-left:4px;">Analysis</td>
            <td style="color:#888;">GPT-4.1-mini + Modal relevance scorer</td>
        </tr>
        <tr>
            <td style="color:#00dd00; font-weight:600; padding-left:4px;">Planning</td>
            <td style="color:#888;">Autonomous GPT tool calling</td>
        </tr>
        <tr>
            <td style="color:#87CEEB; font-weight:600; padding-left:4px;">Messenger</td>
            <td style="color:#888;">Pushover push notifications + LLM copy</td>
        </tr>
    </table>
</div>
"""


def logs_html(log_data):
    output = "<br>".join(log_data[-22:])
    return (
        '<div style="height:350px; overflow-y:auto; border:1px solid #333; '
        "background:rgba(20,20,35,0.95); padding:10px; border-radius:6px; "
        'font-size:11.5px; font-family:monospace; line-height:1.7;">'
        f"{output}</div>"
    )


class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))


def setup_logging(log_queue):
    handler = QueueHandler(log_queue)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    )
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)



class App:
    def __init__(self):
        self.framework = None

    def get_framework(self):
        if not self.framework:
            self.framework = NewsFramework()
        return self.framework

    def table_for(self, opps):
        seen = set()
        rows = []
        for opp in opps:
            if opp.article.url in seen:
                continue
            seen.add(opp.article.url)
            rows.append([
                opp.article.title,
                opp.article.source or "N/A",
                f"{opp.importance:.1f}",
                "Yes" if opp.alerted else "-",
                f"[Link]({opp.article.url})",
            ])
        return rows

    def current_stats(self):
        fw = self.get_framework()
        return make_stats_html(len(fw.memory), fw.alerts_sent, fw.knowledge_size(), fw.last_scan)

    def update_output(self, log_data, log_queue, result_queue):
        initial_table = self.table_for(self.get_framework().memory)
        initial_stats = self.current_stats()
        final_result = None
        while True:
            try:
                message = log_queue.get_nowait()
                log_data.append(reformat(message))
                yield log_data, logs_html(log_data), final_result or initial_table, initial_stats
            except queue.Empty:
                try:
                    final_result, final_stats = result_queue.get_nowait()
                    yield log_data, logs_html(log_data), final_result, final_stats
                except queue.Empty:
                    if final_result is not None:
                        break
                    time.sleep(0.1)

    def do_run(self):
        opps = self.get_framework().run()
        return self.table_for(opps), self.current_stats()

    def run_with_logging(self, initial_log_data):
        log_queue = queue.Queue()
        result_queue = queue.Queue()
        setup_logging(log_queue)

        def worker():
            try:
                result = self.do_run()
                result_queue.put(result)
            except Exception as e:
                logging.error(f"Scan cycle failed: {e}")
                result_queue.put((self.table_for(self.get_framework().memory), self.current_stats()))

        thread = threading.Thread(target=worker)
        thread.start()

        for log_data, output, table, stats in self.update_output(
            initial_log_data, log_queue, result_queue
        ):
            yield log_data, output, table, stats

    def do_select(self, selected_index: gr.SelectData):
        opps = self.get_framework().memory
        row = selected_index.index[0]
        if row < len(opps):
            opp = opps[row]
            self.get_framework().planner.messenger.notify(
                opp.article.title, opp.article.summary, opp.importance, opp.article.url
            )

    def run(self):
        with gr.Blocks(
            title="NewsHound",
            theme=gr.themes.Soft(primary_hue="cyan", neutral_hue="slate"),
            fill_width=True,
        ) as ui:
            log_data = gr.State([])

            gr.HTML(HEADER_HTML)
            stats = gr.HTML(value=make_stats_html(0, 0, 0))

            with gr.Row():
                table = gr.Dataframe(
                    headers=["Title", "Source", "Importance", "Alerted", "URL"],
                    datatype=["str", "str", "str", "str", "markdown"],
                    wrap=True,
                    column_widths=[5, 1, 1, 1, 3],
                    row_count=8,
                    col_count=5,
                    max_height=320,
                )

            with gr.Row():
                with gr.Column(scale=2):
                    gr.HTML(
                        '<div style="color:#e0e0e0; font-size:14px; '
                        'font-weight:600; margin-bottom:4px;">Agent Activity</div>'
                    )
                    logs = gr.HTML()
                with gr.Column(scale=1):
                    gr.HTML(PIPELINE_HTML)

            ui.load(
                self.run_with_logging,
                inputs=[log_data],
                outputs=[log_data, logs, table, stats],
            )

            timer = gr.Timer(value=SCAN_INTERVAL, active=True)
            timer.tick(
                self.run_with_logging,
                inputs=[log_data],
                outputs=[log_data, logs, table, stats],
            )

            table.select(self.do_select)

        ui.launch(share=False, inbrowser=True)


if __name__ == "__main__":
    App().run()
