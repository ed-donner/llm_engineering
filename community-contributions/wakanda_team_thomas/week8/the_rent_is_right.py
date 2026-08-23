import threading
import logging
import queue
import gradio as gr
import plotly.graph_objects as go
from dotenv import load_dotenv
load_dotenv()
from rental_agent_framework import RentalAgentFramework
from agents.rental_deals import RentalOpportunity


class QueueHandler(logging.Handler):
    """Routes log messages to a queue for real-time display in Gradio."""

    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))


class App:
    def __init__(self):
        self.framework = None
        self.opportunities: list[RentalOpportunity] = []
        self.log_queue = queue.Queue()
        self._setup_logging()

    def _setup_logging(self):
        handler = QueueHandler(self.log_queue)
        handler.setFormatter(logging.Formatter("%(message)s"))
        root = logging.getLogger()
        root.addHandler(handler)
        root.setLevel(logging.INFO)

    def _drain_logs(self) -> str:
        lines = []
        while not self.log_queue.empty():
            try:
                lines.append(self.log_queue.get_nowait())
            except queue.Empty:
                break
        return "\n".join(lines)

    def initialize(self):
        self.framework = RentalAgentFramework()
        return "Framework initialized. Ready to hunt deals."

    def hunt_deals(self):
        if not self.framework:
            self.initialize()
        self.opportunities = self.framework.run()
        return self._build_table(), self._drain_logs()

    def _build_table(self) -> list[list]:
        rows = []
        for opp in sorted(self.opportunities, key=lambda o: o.monthly_savings, reverse=True):
            rows.append([
                opp.deal.title,
                opp.deal.city,
                f"${opp.deal.rent:,.0f}",
                f"${opp.estimated_fair_rent:,.0f}",
                f"${opp.monthly_savings:,.0f}",
                opp.deal.url,
            ])
        return rows

    def send_alert(self, evt: gr.SelectData):
        if not self.framework or evt.index[0] >= len(self.opportunities):
            return "No deal selected."
        sorted_opps = sorted(self.opportunities, key=lambda o: o.monthly_savings, reverse=True)
        opp = sorted_opps[evt.index[0]]
        self.framework.messenger.alert(opp)
        return f"Alert sent for: {opp.deal.title}"

    def get_plot(self):
        if not self.framework:
            return go.Figure()
        data = self.framework.plot_data()
        if not data["x"]:
            return go.Figure(layout=go.Layout(title="No data in vector DB yet"))
        fig = go.Figure(data=[go.Scatter3d(
            x=data["x"], y=data["y"], z=data["z"],
            mode="markers",
            marker=dict(size=3, color=data["color"], opacity=0.7),
            text=data["text"],
            hoverinfo="text",
        )])
        fig.update_layout(
            title="Rental Listings Vector Space",
            scene=dict(xaxis_title="PC1", yaxis_title="PC2", zaxis_title="PC3"),
            height=500,
        )
        return fig


def create_ui():
    app = App()

    with gr.Blocks(title="The Rent Is Right") as demo:
        gr.Markdown("# The Rent Is Right\n**Multi-agent rental deal hunter for New York, Lagos, and Nairobi**")

        with gr.Row():
            hunt_btn = gr.Button("Hunt Deals", variant="primary")
            plot_btn = gr.Button("Show Vector Space")

        with gr.Row():
            with gr.Column(scale=2):
                table = gr.Dataframe(
                    headers=["Title", "City", "Listed Rent", "Fair Rent", "Savings", "URL"],
                    label="Discovered Opportunities (click a row to send alert)",
                    interactive=False,
                )
            with gr.Column(scale=1):
                log_output = gr.Textbox(label="Agent Log", lines=15, interactive=False)

        alert_status = gr.Textbox(label="Alert Status", interactive=False)
        plot_output = gr.Plot(label="Vector Database Visualization")

        hunt_btn.click(fn=app.hunt_deals, outputs=[table, log_output])
        table.select(fn=app.send_alert, outputs=[alert_status])
        plot_btn.click(fn=app.get_plot, outputs=[plot_output])

    return demo


if __name__ == "__main__":
    demo = create_ui()
    demo.launch()
