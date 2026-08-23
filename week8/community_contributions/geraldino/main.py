"""
This file is the main file for the Smart Deal Digest.
Gradio UI + pipeline orchestrator.

Run:  python main.py
"""

import json
import logging
import os
import queue
import sys
import threading
import time
from typing import List


import gradio as gr
from dotenv import load_dotenv


from agent.agents import Opportunity, Deal, ScannerAgent, PricerAgent, MessagingAgent


load_dotenv(override=True)

# ANSI colour helpers for logging
BG_BLUE, WHITE, GREEN, RED, RESET = "\033[44m", "\033[37m", "\033[32m", "\033[31m", "\033[0m"
COLOR_MAP = {
    BG_BLUE + WHITE: '<span style="color:#ff7800">',
    GREEN:           '<span style="color:#00dd00">',
    RED:             '<span style="color:#dd0000">',
}

def reformat(message: str) -> str:
    for code, tag in COLOR_MAP.items():
        message = message.replace(code, tag)
    return message.replace(RESET, "</span>")

MEMORY_FILE = "memory.json"


# Framework that owns the three agents and memory.
class DealDigestFramework:
    """
    Owns the three agents and memory.
    .run() → full pipeline → returns updated memory (list of Opportunity).
    """

    def __init__(self):
        self.scanner   = ScannerAgent()
        self.pricer    = PricerAgent()
        self.messenger = MessagingAgent()
        self.memory: List[Opportunity] = self._read_memory()
        self._log(f"Framework ready — {len(self.memory)} deals in memory")

    def _log(self, msg: str):
        logging.info(BG_BLUE + WHITE + f"[Framework] {msg}" + RESET)

    def _read_memory(self) -> List[Opportunity]:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE) as f:
                return [Opportunity(**item) for item in json.load(f)]
        return []

    def _write_memory(self):
        with open(MEMORY_FILE, "w") as f:
            json.dump([o.model_dump() for o in self.memory], f, indent=2)

    
    
    def run(self) -> List[Opportunity]:
        """Scanner → Pricer → Messenger → persist to memory.json"""
        self._log("Starting pipeline…")

        selection     = self.scanner.scan(show_progress=False)
        opportunities = self.pricer.price(selection)

        if opportunities:
            self.messenger.send_digest(opportunities)
            for opp in opportunities:
                self.memory.append(opp)
            self._write_memory()
            self._log(f"Pipeline done — {len(opportunities)} new opportunities added")
        else:
            self._log("Pipeline done — no opportunities this run")

        return self.memory


# Logging queue handler that is used to stream logs to the UI.
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))


def setup_logging(log_queue):
    root = logging.getLogger()
    # Remove any existing QueueHandlers first
    root.handlers = [h for h in root.handlers if not isinstance(h, QueueHandler)]
    handler = QueueHandler(log_queue)
    formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def html_for(log_data: list) -> str:
    output = "<br>".join(log_data[-18:])
    return f"""<div style="height:380px;overflow-y:auto;border:1px solid #ccc;
        background:#222229;padding:10px;font-size:12px;font-family:monospace;color:#ffffff">
        {output}</div>"""


# Gradio App that is used to display the UI.
class App:
    def __init__(self):
        self.framework = None

    def get_framework(self):
        if not self.framework:
            self.framework = DealDigestFramework()
        return self.framework

    js = "() => { document.querySelector('body').classList.add('dark'); }"

    def run(self):
        with gr.Blocks(title="Smart Deal Alert", fill_width=True, theme=gr.themes.Default()) as ui:
            log_data = gr.State([])

            # Helpers for the UI.
            def table_for(opps: List[Opportunity]):
                return [
                    [
                        opp.deal.product_description,
                        f"${opp.deal.price:.2f}",
                        f"${opp.estimate:.2f}",
                        f"${opp.discount:.2f}",
                        opp.deal.url,
                    ]
                    for opp in opps[-5:]
                ]

            def update_output(log_data, log_queue, result_queue):
                """Stream log messages and yield table updates."""
                initial = table_for(self.get_framework().memory)
                final   = None
                while True:
                    try:
                        msg = log_queue.get_nowait()
                        log_data.append(reformat(msg))
                        yield log_data, html_for(log_data), final or initial
                    except queue.Empty:
                        try:
                            final = result_queue.get_nowait()
                            yield log_data, html_for(log_data), final
                        except queue.Empty:
                            if final is not None:
                                break
                            time.sleep(0.1)

            def run_with_logging(initial_log_data):
                """Run pipeline in background thread, stream logs to UI — mirrors Ed's pattern."""
                log_queue    = queue.Queue()
                result_queue = queue.Queue()
                setup_logging(log_queue)

                def worker():
                    result = table_for(self.get_framework().run())
                    result_queue.put(result)

                threading.Thread(target=worker).start()
                yield from update_output(initial_log_data, log_queue, result_queue)

            def do_select(selected_index: gr.SelectData):
                """Click a deal row → send email alert — mirrors Ed's do_select."""
                opps = self.get_framework().memory
                if selected_index.index[0] < len(opps):
                    opp = opps[selected_index.index[0]]
                    self.get_framework().messenger.alert(opp)

            # UI Display elements.
            with gr.Row():
                gr.Markdown(
                    '<div style="text-align:center;font-size:24px">'
                    '<strong>Smart Deal Alert</strong> — AI-Powered Deal Hunter</div>'
                )
            with gr.Row():
                gr.Markdown(
                    '<div style="text-align:center;font-size:14px;color:#888">'
                    'Fine-tuned Qwen2.5B estimates real value · '
                    'GPT-4o-mini selects quality deals · '
                    'Click any row to get an email alert</div>'
                )
            with gr.Row():
                opportunities_dataframe = gr.Dataframe(
                    headers=["Product", "Listed Price", "Estimated Value", "You Save", "URL"],
                    wrap=True,
                    column_widths=[6, 1, 1, 1, 3],
                    row_count=10,
                    col_count=5,
                    max_height=400,
                )
            with gr.Row():
                logs = gr.HTML(label="Agent logs")

            # Auto-run loaded + every 90 seconds.
            ui.load(run_with_logging, inputs=[log_data],
                    outputs=[log_data, logs, opportunities_dataframe])

            gr.Timer(value=90, active=True).tick(
                run_with_logging, inputs=[log_data],
                outputs=[log_data, logs, opportunities_dataframe]
            )

            opportunities_dataframe.select(do_select)

        ui.launch(share=False, inbrowser=True)


if __name__ == "__main__":
    App().run()
