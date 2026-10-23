# ---------------------
# Main App Driver
# ---------------------

from helpers.functional import print_title
from helpers.system_settings import get_system_settings
system_settings = get_system_settings()

from core.database import csv_to_sqlite

from pathlib import Path



def ask(input_type, text, audio_path):
    try:
        plot_dir = Path(system_settings.PLOTS_PATH)
        before = {
            path: (path.stat().st_mtime_ns, path.stat().st_size)
            for path in plot_dir.glob("plot*.png") if path.is_file()
        }
        if input_type == "Text":
            if not text or not text.strip():
                raise gr.Error("Please type your question.")
            response = run_orchestrator(user_prompt=text.strip())
        else:
            if not audio_path:
                raise gr.Error("Please record your question first.")
            response = run_orchestrator(voice_path=audio_path)

        plots = [
            str(path) for path in sorted(plot_dir.glob("plot*.png"))
            if path.is_file()
            and before.get(path) != (path.stat().st_mtime_ns, path.stat().st_size)
        ]
        return response, plots

    except gr.Error:
        raise
    except Exception as error:
        raise gr.Error(f"{type(error).__name__}: {error}")


def toggle_inputs(input_type):
    return gr.update(visible=input_type == "Text"), gr.update(visible=input_type == "Audio")


if __name__ == "__main__":
    print_title("Preparing the Database...")


    n_rows = csv_to_sqlite(
        csv_path=system_settings.CSV_PATH,
        db_path=system_settings.DB_PATH,
        table_name='products'
    )
    print(f"N.Rows: {n_rows}")


    print_title("Initiating the APP...")

    from llms.orchestrator import run_orchestrator
    import gradio as gr

    with gr.Blocks(title="Data Analyst Assistant") as app:
        gr.Markdown("# Data Analyst Assistant\n")

        input_type = gr.Radio(["Text", "Audio"], value="Text", label="Input type")

        text_input = gr.Textbox(label="Your question", lines=4, placeholder="e.g. Which vendor sells the cheapest smart watch?", visible=True)
        audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Record your question", visible=False)
        
        submit = gr.Button("Ask", variant="primary")
        output_height = 500
        with gr.Row():
            with gr.Column(scale=1):
                answer = gr.Markdown(
                    label="Answer", container=True, padding=True,
                    height=output_height, max_height=output_height,
                )
            with gr.Column(scale=1):
                plots = gr.Gallery(
                    label="Generated plots", columns=1, rows=1,
                    type="filepath", height=output_height,
                    object_fit="contain", preview=True,
                )

        input_type.change(toggle_inputs, inputs=input_type, outputs=[text_input, audio_input])
        submit.click(
            ask, inputs=[input_type, text_input, audio_input],
            outputs=[answer, plots], concurrency_limit=1,
        )

    app.launch()

