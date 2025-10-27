import atexit
import os

import gradio as gr
import openai
from dotenv import load_dotenv

from src.constants import PROJECT_TEMP_DIR, SYSTEM_PROMPT, USER_PROMPT
from src.data_generation import generate_and_evaluate_data
from src.IO_utils import cleanup_temp_files
from src.plot_utils import display_reference_csv


def main():
    # ==========================================================
    # Setup
    # ==========================================================

    # Load the api key
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Temporary folder for images
    os.makedirs(PROJECT_TEMP_DIR, exist_ok=True)

    # Ensure temporary plot images are deleted when the program exits
    atexit.register(lambda: cleanup_temp_files(PROJECT_TEMP_DIR))

    # ==========================================================
    # Gradio App
    # ==========================================================
    with gr.Blocks() as demo:

        # Store temp folder in state
        temp_dir_state = gr.State(value=PROJECT_TEMP_DIR)

        gr.Markdown("# 🧠 Synthetic Data Generator (with OpenAI)")

        # ======================================================
        # Tabs for organized sections
        # ======================================================
        with gr.Tabs():

            # ------------------------------
            # Tab 1: Input
            # ------------------------------
            with gr.Tab("Input"):

                # System prompt in collapsible
                with gr.Accordion("System Prompt (click to expand)", open=False):
                    system_prompt_input = gr.Textbox(
                        label="System Prompt", value=SYSTEM_PROMPT, lines=20
                    )

                # User prompt box
                user_prompt_input = gr.Textbox(
                    label="User Prompt", value=USER_PROMPT, lines=5
                )

                # Model selection
                model_select = gr.Dropdown(
                    label="OpenAI Model",
                    choices=["gpt-4o-mini", "gpt-4.1-mini"],
                    value="gpt-4o-mini",
                )

                # Reference CSV upload
                reference_input = gr.File(
                    label="Reference CSV (optional)", file_types=[".csv"]
                )

                # Examples
                gr.Examples(
                    examples=[
                        "data/sentiment_reference.csv",
                        "data/people_reference.csv",
                        "data/wine_reference.csv",
                    ],
                    inputs=reference_input,
                )

                # Generate button
                generate_btn = gr.Button("🚀 Generate Data")

                # Download button
                download_csv = gr.File(label="Download CSV")

            # ------------------------------
            # Tab 2: Reference Table
            # ------------------------------
            with gr.Tab("Reference Table"):
                reference_display = gr.DataFrame(label="Reference CSV Preview")

            # ------------------------------
            # Tab 3: Generated Table
            # ------------------------------
            with gr.Tab("Generated Table"):
                output_df = gr.DataFrame(label="Generated Data")

            # ------------------------------
            # Tab 4: Evaluation
            # ------------------------------
            with gr.Tab("Comparison"):
                with gr.Accordion("Evaluation Results (click to expand)", open=True):
                    evaluation_df = gr.DataFrame(label="Evaluation Results")

            # ------------------------------
            # Tab 5: Visualizations
            # ------------------------------

            with gr.Tab("Visualizations"):
                gr.Markdown("# Click on the box to expand")

                images_gallery = gr.Gallery(
                    label="Column Visualizations",
                    show_label=True,
                    columns=2,
                    height="auto",
                    interactive=True,
                )

            # Hidden state for internal use
            generated_state = gr.State()

        # ======================================================
        # Event bindings
        # ======================================================
        generate_btn.click(
            fn=generate_and_evaluate_data,
            inputs=[
                system_prompt_input,
                user_prompt_input,
                temp_dir_state,
                reference_input,
                model_select,
            ],
            outputs=[
                output_df,
                download_csv,
                evaluation_df,
                generated_state,
                images_gallery,
            ],
        )

        reference_input.change(
            fn=display_reference_csv,
            inputs=[reference_input],
            outputs=[reference_display],
        )

    demo.launch(debug=True)


if __name__ == "__main__":
    main()
