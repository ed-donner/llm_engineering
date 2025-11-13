import gradio as gr
from src.gradio_core.gradio_docstring import (gradio_scan_and_generate,  
                                              next_item, 
                                              accept_all)
from src.gradio_core.gradio_unit_test import gradio_generate_unit_tests
from constants import models

# ============================================================
# UI Tab: Docstring Generator
# ============================================================

def build_docstring_tab():
    with gr.Tab("Docstring Generator"):
        gr.Markdown("### Generate and review Python docstrings")

        with gr.Group():
            with gr.Row():
                folder_input = gr.Textbox(label="Folder path", placeholder="Path to your Python folder")
                project_input = gr.Textbox(label="Project root path", placeholder="Root path (Optional for indexing)")
            with gr.Row():
                model_selector = gr.Dropdown(label="Model", choices=models, value=models[0])
                names_input = gr.Textbox(label="Names (comma-separated)", placeholder="e.g. foo,bar,BazClass")

        scan_btn = gr.Button("🔍 Scan & Generate")

        # Docstring preview/edit
        with gr.Row():
            original_box = gr.Textbox(label="Original Docstring", lines=5)
            suggested_box = gr.Textbox(label="Suggested Docstring (editable)", lines=5)

        # Action buttons
        with gr.Row():
            accept_btn = gr.Button("✅ Accept")
            skip_btn = gr.Button("➡️ Skip")
            accept_all_btn = gr.Button("🚀 Accept All")

        # Status & source
        status_box = gr.Textbox(label="Status", interactive=False)
        source_box = gr.Code(label="Function/Class Source", lines=10)

        # Internal state
        state_results = gr.State()
        state_index = gr.State()

        # Button callbacks
        scan_btn.click(
            fn=gradio_scan_and_generate,
            inputs=[folder_input, model_selector, names_input, project_input],
            outputs=[original_box, suggested_box, source_box, state_index, state_results, status_box],
        )

        accept_btn.click(
            fn=next_item,
            inputs=[gr.State("Accept"), suggested_box, state_results, state_index],
            outputs=[original_box, suggested_box, source_box, state_index, state_results, status_box],
        )

        skip_btn.click(
            fn=next_item,
            inputs=[gr.State("Skip"), suggested_box, state_results, state_index],
            outputs=[original_box, suggested_box, source_box, state_index, state_results, status_box],
        )

        accept_all_btn.click(
            fn=accept_all,
            inputs=[suggested_box, state_results, state_index],
            outputs=[original_box, suggested_box, source_box, state_index, state_results, status_box],
        )

# ============================================================
# UI Tab: Unit Test Generator
# ============================================================

def build_tests_tab():
    with gr.Tab("Unit Test Generator"):
        gr.Markdown("### Generate pytest-style unit tests from your project")

        with gr.Group():
            with gr.Row():
                folder_input = gr.Textbox(label="Folder path", placeholder="Path to the file or folder to test")
                project_input = gr.Textbox(label="Project root path (required)", placeholder="Root path of your project")
            with gr.Row():
                model_selector = gr.Dropdown(label="Model", choices=models, value=models[3])
                names_input = gr.Textbox(label="Function/Class names (optional)", placeholder="e.g. foo,bar,BazClass")

        generate_btn = gr.Button("Generate Tests")
        status_box = gr.Textbox(label="Status", interactive=False, lines=5)

        generate_btn.click(
            fn=gradio_generate_unit_tests,
            inputs=[folder_input, model_selector, names_input, project_input],
            outputs=status_box,
        )

# ============================================================
# Launch Gradio App
# ============================================================

with gr.Blocks() as app:
    gr.Markdown("# AI Docstring and Unit Test Generator")
    build_docstring_tab()
    build_tests_tab()

if __name__ == "__main__":
    app.launch(inbrowser=True)
