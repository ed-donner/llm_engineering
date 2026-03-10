import logging
import queue
import threading
import time
import gradio as gr
from job_agent_framework import JobAgentFramework
from log_utils import reformat
from dotenv import load_dotenv

load_dotenv(override=True)


class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))


def html_for(log_data):
    output = "<br>".join(log_data[-18:])
    return f"""
    <div id="scrollContent" style="height: 400px; overflow-y: auto; border: 1px solid #ccc; background-color: #222229; padding: 10px;">
    {output}
    </div>
    """


def setup_logging(log_queue):
    handler = QueueHandler(log_queue)
    formatter = logging.Formatter(
        "[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class App:
    def __init__(self):
        self.agent_framework = None

    def get_agent_framework(self):
        if not self.agent_framework:
            self.agent_framework = JobAgentFramework()
        return self.agent_framework

    def run(self):
        with gr.Blocks(title="The Salary Is Right", fill_width=True) as ui:
            log_data = gr.State([])

            def table_for(opps):
                return [
                    [
                        opp.listing.job_title,
                        opp.listing.company,
                        f"${opp.listing.salary:,.0f}",
                        f"${opp.estimate:,.0f}",
                        f"${opp.premium:,.0f}",
                        opp.listing.location,
                        opp.listing.url,
                    ]
                    for opp in opps
                ]

            def update_output(log_data, log_queue, result_queue):
                initial_result = table_for(self.get_agent_framework().memory)
                final_result = None
                while True:
                    try:
                        message = log_queue.get_nowait()
                        log_data.append(reformat(message))
                        yield log_data, html_for(log_data), final_result or initial_result
                    except queue.Empty:
                        try:
                            final_result = result_queue.get_nowait()
                            yield log_data, html_for(log_data), final_result or initial_result
                        except queue.Empty:
                            if final_result is not None:
                                break
                            time.sleep(0.1)

            def do_run():
                new_opportunities = self.get_agent_framework().run()
                return table_for(new_opportunities)

            def run_with_logging(initial_log_data):
                log_queue = queue.Queue()
                result_queue = queue.Queue()
                setup_logging(log_queue)

                def worker():
                    result = do_run()
                    result_queue.put(result)

                thread = threading.Thread(target=worker)
                thread.start()

                for ld, output, final_result in update_output(
                    initial_log_data, log_queue, result_queue
                ):
                    yield ld, output, final_result

            def do_select(selected_index: gr.SelectData):
                opportunities = self.get_agent_framework().memory
                row = selected_index.index[0]
                opportunity = opportunities[row]
                self.get_agent_framework().planner.messenger.alert(opportunity)

            with gr.Row():
                gr.Markdown(
                    '<div style="text-align: center;font-size:24px">'
                    "<strong>The Salary Is Right</strong> - "
                    "Autonomous Agent Framework that hunts for salary opportunities"
                    "</div>"
                )
            with gr.Row():
                gr.Markdown(
                    '<div style="text-align: center;font-size:14px">'
                    "A fine-tuned LLM on Modal and a RAG pipeline with a frontier model "
                    "collaborate to find above-market salary opportunities and send "
                    "push notifications."
                    "</div>"
                )
            with gr.Row():
                opportunities_dataframe = gr.Dataframe(
                    headers=[
                        "Job Title", "Company", "Offered Salary",
                        "Market Estimate", "Premium", "Location", "URL",
                    ],
                    wrap=True,
                    column_widths=[3, 2, 1, 1, 1, 2, 3],
                    row_count=10,
                    col_count=7,
                    max_height=400,
                )
            with gr.Row():
                logs = gr.HTML()

            ui.load(
                run_with_logging,
                inputs=[log_data],
                outputs=[log_data, logs, opportunities_dataframe],
            )

            timer = gr.Timer(value=300, active=True)
            timer.tick(
                run_with_logging,
                inputs=[log_data],
                outputs=[log_data, logs, opportunities_dataframe],
            )

            opportunities_dataframe.select(do_select)

        ui.launch(share=False, inbrowser=True)


if __name__ == "__main__":
    App().run()
