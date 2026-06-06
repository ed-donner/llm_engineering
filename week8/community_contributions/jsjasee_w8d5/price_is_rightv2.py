import logging
import queue
import threading
import time
import gradio as gr
from deal_agent_framework import DealAgentFramework
from log_utils import reformat
import plotly.graph_objects as go
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
        # ⭐️ added some states to App
        self.log_data = []
        self.latest_table = []
        self.agent_running = False
        self.lock = threading.Lock()  # what does this do??
        self.log_queue = queue.Queue()

        self.stop_event = threading.Event()

    def agent_loop(self):
        # ⭐️ make a background loop, which is better than while True: time.sleep(300) because stop_event.wait(300) can be stopped cleanly later. - how so?
        while not self.stop_event.is_set():
            with self.lock:
                already_running = self.agent_running

            if not already_running:
                with self.lock:
                    self.agent_running = True

                try:
                    opportunities = self.get_agent_framework().run()
                    table = [
                        [
                            opp.deal.product_description,
                            f"${opp.deal.price:.2f}",
                            f"${opp.estimate:.2f}",
                            f"${opp.discount:.2f}",
                            opp.deal.url,
                        ]
                        for opp in opportunities
                    ]

                    with self.lock:
                        self.latest_table = table

                except Exception as e:
                    logging.exception(f"Agent run failed: {e}")

                finally:
                    with self.lock:
                        self.agent_running = False

            self.stop_event.wait(300)

    def get_agent_framework(self):
        if not self.agent_framework:
            self.agent_framework = DealAgentFramework()
        return self.agent_framework

    def run(self):
        with gr.Blocks(title="The Price is Right", fill_width=True) as ui:
            log_data = gr.State([])

            # ⭐️ make gradio only refresh the ui
            def refresh_ui():
                # 1. DRAIN: pull everything that piled up since the last tick
                while True:
                    try:
                        message = self.log_queue.get_nowait()  # non-blocking grab
                    except queue.Empty:
                        break  # nothing left -> stop
                    self.log_data.append(
                        reformat(message)
                    )  # add it to our running list

                # 2. read the shared table safely (the agent loop thread writes to this table once the deal is fetched, then we write the latest one)
                with self.lock:
                    table = self.latest_table

                return html_for(self.log_data), table

            def table_for(opps):
                return [
                    [
                        opp.deal.product_description,
                        f"${opp.deal.price:.2f}",
                        f"${opp.estimate:.2f}",
                        f"${opp.discount:.2f}",
                        opp.deal.url,
                    ]
                    for opp in opps
                ]

            def get_initial_plot():
                fig = go.Figure()
                fig.update_layout(
                    title="Loading vector DB...",
                    height=400,
                )
                return fig

            def get_plot():
                documents, vectors, colors = DealAgentFramework.get_plot_data(
                    max_datapoints=800
                )
                # Create the 3D scatter plot
                fig = go.Figure(
                    data=[
                        go.Scatter3d(
                            x=vectors[:, 0],
                            y=vectors[:, 1],
                            z=vectors[:, 2],
                            mode="markers",
                            marker=dict(size=2, color=colors, opacity=0.7),
                        )
                    ]
                )

                fig.update_layout(
                    scene=dict(
                        xaxis_title="x",
                        yaxis_title="y",
                        zaxis_title="z",
                        aspectmode="manual",
                        aspectratio=dict(
                            x=2.2, y=2.2, z=1
                        ),  # Make x-axis twice as long
                        camera=dict(
                            eye=dict(x=1.6, y=1.6, z=0.8)  # Adjust camera position
                        ),
                    ),
                    height=400,
                    margin=dict(r=5, b=1, l=5, t=2),
                )

                return fig

            def do_select(selected_index: gr.SelectData):
                opportunities = self.get_agent_framework().memory
                row = selected_index.index[0]
                opportunity = opportunities[row]
                self.get_agent_framework().planner.messenger.alert(opportunity)

            with gr.Row():
                gr.Markdown(
                    '<div style="text-align: center;font-size:24px"><strong>The Price is Right</strong> - Autonomous Agent Framework that hunts for deals</div>'
                )
            with gr.Row():
                gr.Markdown(
                    '<div style="text-align: center;font-size:14px">A proprietary fine-tuned LLM deployed on Modal and a RAG pipeline with a frontier model collaborate to send push notifications with great online deals.</div>'
                )
            with gr.Row():
                opportunities_dataframe = gr.Dataframe(
                    headers=[
                        "Deals found so far",
                        "Price",
                        "Estimate",
                        "Discount",
                        "URL",
                    ],
                    wrap=True,
                    column_widths=[6, 1, 1, 1, 3],
                    row_count=10,
                    col_count=5,
                    max_height=400,
                )
            with gr.Row():
                with gr.Column(scale=1):
                    logs = gr.HTML()
                with gr.Column(scale=1):
                    plot = gr.Plot(value=get_plot(), show_label=False)

            # timer should ONLY refresh the UI
            timer = gr.Timer(value=5, active=True)

            timer.tick(
                refresh_ui,
                outputs=[logs, opportunities_dataframe],
            )

            opportunities_dataframe.select(do_select)

        # improvements:
        setup_logging(self.log_queue)  # 1. plumbing, once
        self.latest_table = table_for(
            self.get_agent_framework().memory
        )  # 2. seed so it's not blank

        # ⭐️ start the thread right before ui launch, start the one worker only
        threading.Thread(target=self.agent_loop, daemon=True).start()
        ui.launch(share=False, inbrowser=True)


if __name__ == "__main__":
    App().run()
