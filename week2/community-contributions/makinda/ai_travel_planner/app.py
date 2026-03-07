"""Gradio web interface for AI Travel Planner."""
import gradio as gr

from planner import generate_travel_plan


def plan_callback(destination: str, days: int, budget: float | int) -> str:
    if not destination or not days or not budget:
        return "Please fill Destination, Days, and Budget."
    days, budget = int(days), int(budget)
    if days < 1 or days > 30 or budget < 1:
        return "Days (1–30) and Budget must be positive."
    return generate_travel_plan(destination.strip(), days, budget, user_id="gradio")


def build_and_launch():
    with gr.Blocks(title="AI Travel Planner") as ui:
        gr.Markdown("# AI Travel Planner")
        dest = gr.Textbox(label="Destination", placeholder="e.g. Mombasa")
        days = gr.Number(label="Number of days", value=3, minimum=1, maximum=30, step=1)
        budget = gr.Number(label="Budget (USD)", value=1000, minimum=1, step=1)
        out = gr.Textbox(label="Itinerary", lines=20)
        btn = gr.Button("Generate plan")
        btn.click(fn=plan_callback, inputs=[dest, days, budget], outputs=out)
    ui.launch()


if __name__ == "__main__":
    build_and_launch()
