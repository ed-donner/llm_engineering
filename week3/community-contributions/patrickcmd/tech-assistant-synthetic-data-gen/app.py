import gradio as gr
import pandas as pd

from llm_clients import MODELS
from prompt_builder import ENGINEER_LEVELS
from generator import generate_dataset
from hf_uploader import upload_to_huggingface

TOPICS = [
    "RAG systems",
    "LLM inference",
    "Prompt engineering",
    "Fine-tuning",
    "Evaluation methods",
    "Vector databases",
    "Embeddings",
    "Tokenization",
    "Model architecture",
    "Training pipelines",
    "GPU optimization",
    "Quantization",
    "Agent frameworks",
]

generated_df: pd.DataFrame = pd.DataFrame()


def on_generate(model_key, engineer_level, topic, dataset_size, temperature, progress=gr.Progress()):
    global generated_df

    if not model_key or not engineer_level or not topic:
        gr.Warning("Please fill in all required fields.")
        return pd.DataFrame()

    dataset_size = int(dataset_size)

    def progress_callback(current, total):
        progress(current / total, desc=f"Generated {current}/{total} datapoints")

    generated_df = generate_dataset(
        model_key=model_key,
        topic=topic,
        engineer_level=engineer_level,
        dataset_size=dataset_size,
        temperature=temperature,
        progress_callback=progress_callback,
    )

    if generated_df.empty:
        gr.Warning("No datapoints were generated. Try again or switch models.")
        return pd.DataFrame()

    gr.Info(f"Generated {len(generated_df)} datapoints.")
    return generated_df


def on_upload(hf_username, hf_token, dataset_name):
    global generated_df

    if generated_df.empty:
        gr.Warning("Generate a dataset first.")
        return "No dataset to upload."

    if not hf_username or not hf_token or not dataset_name:
        gr.Warning("Please fill in all HuggingFace fields.")
        return "Missing HuggingFace credentials."

    try:
        url = upload_to_huggingface(generated_df, hf_username, hf_token, dataset_name)
        return f"Uploaded successfully: {url}"
    except Exception as e:
        return f"Upload failed: {e}"


def build_ui():
    with gr.Blocks(title="Synthetic Dataset Generator", theme=gr.themes.Soft()) as app:
        gr.Markdown("# Technical Assistant Dataset Generator")
        gr.Markdown("Generate synthetic training data for AI Engineering assistants.")

        with gr.Row():
            with gr.Column():
                model_dropdown = gr.Dropdown(
                    choices=list(MODELS.keys()),
                    label="Model",
                    value="gpt-4.1-mini",
                )
                level_dropdown = gr.Dropdown(
                    choices=list(ENGINEER_LEVELS.keys()),
                    label="Engineer Level",
                    value="intermediate",
                )
                topic_dropdown = gr.Dropdown(
                    choices=TOPICS,
                    label="Topic",
                    value="RAG systems",
                    allow_custom_value=True,
                )
                dataset_size = gr.Slider(
                    minimum=5, maximum=200, value=20, step=5, label="Dataset Size"
                )
                temperature = gr.Slider(
                    minimum=0.0, maximum=1.5, value=0.9, step=0.1, label="Temperature"
                )
                generate_btn = gr.Button("Generate Dataset", variant="primary")

            with gr.Column():
                gr.Markdown("### HuggingFace Upload")
                hf_username = gr.Textbox(label="HF Username", placeholder="your-username")
                hf_token = gr.Textbox(label="HF Token", type="password", placeholder="hf_...")
                dataset_name = gr.Textbox(
                    label="Dataset Name", placeholder="ai-engineer-synthetic-dataset"
                )
                upload_btn = gr.Button("Upload to HuggingFace")
                upload_status = gr.Textbox(label="Upload Status", interactive=False)

        gr.Markdown("### Dataset Preview")
        preview_table = gr.DataFrame(wrap=True)

        generate_btn.click(
            fn=on_generate,
            inputs=[model_dropdown, level_dropdown, topic_dropdown, dataset_size, temperature],
            outputs=[preview_table],
        )
        upload_btn.click(
            fn=on_upload,
            inputs=[hf_username, hf_token, dataset_name],
            outputs=[upload_status],
        )

    return app


if __name__ == "__main__":
    app = build_ui()
    app.launch(inbrowser=True)