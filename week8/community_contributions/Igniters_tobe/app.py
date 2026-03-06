import gradio as gr
import sys
import os

# Ensure the parent directory is in the path so we can import 'Igniters_tobe'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Igniters_tobe.orchestrator import process_research_request
from Igniters_tobe.config import AVAILABLE_MODELS, DEFAULT_MODEL

def run_research_app(query, research_model, fact_checker_model, writer_model):
    if not query.strip():
        yield "Please enter a question.", "No logs available."
        return

    try:
        for answer, logs in process_research_request(
            query,
            research_model=research_model,
            fact_checker_model=fact_checker_model,
            writer_model=writer_model,
        ):
            yield answer, logs
    except Exception as e:
        yield f"An error occurred: {str(e)}", f"Error details: {str(e)}"

# Custom CSS
custom_css = """
body { background-color: #0f172a; color: #f8fafc; }
.gradio-container { border: 1px solid #1e293b; border-radius: 12px; padding: 20px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
#title { text-align: center; color: #38bdf8; font-size: 2.5rem; margin-bottom: 20px; }
#subtitle { text-align: center; color: #94a3b8; margin-bottom: 30px; }
.run-btn { background: linear-gradient(135deg, #38bdf8 0%, #2563eb 100%) !important; border: none !important; color: white !important; }
.run-btn:hover { transform: scale(1.02); transition: all 0.2s ease; }
"""

with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Multi-Agent Research Assistant", elem_id="title")
    gr.Markdown("An AI team working together: **Researcher** then **Fact Checker** then **Writer**", elem_id="subtitle")

    with gr.Row():
        with gr.Column(scale=2):
            input_text = gr.Textbox(
                label="What would you like to research?",
                placeholder="e.g., What are the latest developments in fusion energy?",
                lines=3
            )

    with gr.Accordion("Agent Model Configuration", open=False):
        with gr.Row():
            research_model = gr.Dropdown(
                choices=AVAILABLE_MODELS,
                value=DEFAULT_MODEL,
                label="Research Agent Model",
            )
            fact_checker_model = gr.Dropdown(
                choices=AVAILABLE_MODELS,
                value=DEFAULT_MODEL,
                label="Fact Checker Agent Model",
            )
            writer_model = gr.Dropdown(
                choices=AVAILABLE_MODELS,
                value=DEFAULT_MODEL,
                label="Writer Agent Model",
            )

    run_btn = gr.Button("Run Research", variant="primary", elem_classes="run-btn")

    with gr.Row():
        with gr.Column():
            output_answer = gr.Markdown(label="Final Answer")
        with gr.Column():
            output_logs = gr.Textbox(label="Agent Reasoning Logs", interactive=False, lines=15)

    run_btn.click(
        fn=run_research_app,
        inputs=[input_text, research_model, fact_checker_model, writer_model],
        outputs=[output_answer, output_logs],
    )

if __name__ == "__main__":
    demo.launch()
