import gradio as gr
from test_generator import generate_tests

def create_interface():
    with gr.Blocks(title="Unit Test Generator") as ui:
        gr.Markdown("# Unit Test Generator")
        gr.Markdown("Paste your Python code and get AI-generated unit tests")

        with gr.Row():
            with gr.Column(scale=1):
                code_input = gr.Code(
                    label="Your Code",
                    language="python",
                    lines=15
                )
                generate_btn = gr.Button("Generate Tests", variant="primary")

            with gr.Column(scale=1):
                tests_output = gr.Textbox(
                    label="Generated Tests",
                    lines=15,
                    interactive=False
                )

        generate_btn.click(
            fn=generate_tests,
            inputs=[code_input],
            outputs=[tests_output]
        )

    return ui

def launch():
    ui = create_interface()
    ui.launch(server_name="localhost", server_port=7860)
