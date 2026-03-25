"""Synthetic Dataset Generator with Gradio UI.

The app streams the model's responses to the user. The user passes in a theme
in a text box and clicks 'Propose Schema'; the system calls the LLM and
displays the schema in the next text box. The user defines the number of
examples and clicks 'Generate Dataset'; the system calls the LLM and displays
the dataset. The user can download the dataset in CSV or JSON.
"""

import os
import tempfile
from typing import Literal

import gradio as gr
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI


def stream_response(client: OpenAI, model: str, prompt: list[dict[str, str]]):
    """Stream LLM response chunks and yield accumulated content so far."""
    stream = client.chat.completions.create(
        model=model,
        messages=prompt,
        stream=True,
    )
    accumulated = ""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta is not None:
            accumulated += chunk.choices[0].delta.content or ""
        yield accumulated


def generate_schema(theme: str, model: str):
    """Call the LLM to propose a dataset schema for the given theme."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = [
        {
            "role": "system",
            "content": (
                "You are a data schema generator. Your task is to generate a "
                "dataset schema for a synthetic dataset based on the "
                "user-provided theme. Return the schema WITHOUT any additional "
                "text, examples or comments. Only the schema in a valid JSON "
                "format."
            ),
        },
        {"role": "user", "content": f"Theme: {theme}"},
    ]
    yield from stream_response(client, model, prompt)


def generate_dataset(
    schema: str, num_examples: int, ext: Literal["CSV", "JSON"], model: str
):
    """Call the LLM to generate a synthetic dataset from the schema."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = [
        {
            "role": "system",
            "content": (
                "You are a dataset generator. Your task is to generate a "
                "synthetic dataset based on the user-provided schema and the "
                "required amount of records. Return only data in selected "
                "format WITHOUT any additional comments, examples or text."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Schema: {schema}\nNumber of records: {num_examples}\n"
                f"Return the dataset in a valid {ext} format WITHOUT any "
                "additional comments, examples or text."
            ),
        },
    ]
    yield from stream_response(client, model, prompt)


def download_dataset(
    dataset: str, schema: str, theme: str, ext: Literal["CSV", "JSON"]
):
    """Create a temporary file with schema and dataset for download."""
    with tempfile.NamedTemporaryFile(
        prefix=f"dataset_{theme.replace(' ', '_').lower()}_",
        mode="w+b",
        suffix=f".{ext.lower()}",
        delete=False,
    ) as tmp:
        tmp.write(schema.encode("utf-8"))
        tmp.write("\n\n".encode("utf-8"))
        tmp.write(dataset.encode("utf-8"))
    return tmp.name


def ui():
    """Build and return the Gradio Blocks demo for the dataset generator."""
    with gr.Blocks() as demo:
        gr.Markdown("## Synthetic Dataset Generator")
        with gr.Row():
            theme = gr.Textbox(
                label="Theme",
                placeholder="Enter a theme for the dataset",
                max_lines=1,
            )
            num_examples = gr.Number(
                label="Number of examples",
                placeholder="Enter the number of examples for the dataset",
            )
            format_str = gr.Dropdown(
                label="Format", choices=["csv", "json"]
            )
            model = gr.Dropdown(
                label="Model",
                choices=["gpt-4o-mini", "gpt-4o", "gpt-4o-turbo"],
            )
            schema_button = gr.Button(
                "Propose Schema", variant="primary", size="lg"
            )
        with gr.Row():
            schema_output = gr.Textbox(
                label="Schema",
                placeholder="Enter a schema for the dataset",
                lines=10,
                max_lines=15,
                scale=2,
            )
            dataset_button = gr.Button(
                "Generate Dataset", variant="primary", size="lg", scale=1
            )
        with gr.Row():
            dataset_output = gr.Textbox(
                label="Dataset",
                placeholder="Enter a dataset",
                lines=10,
                max_lines=15,
                scale=2,
            )
            download_button = gr.Button(
                "Download", variant="primary", size="lg", scale=1
            )
        with gr.Row():
            download_output = gr.File(label="Download", visible=True)

        schema_button.click(
            generate_schema,
            inputs=[theme, model],
            outputs=[schema_output],
        )
        dataset_button.click(
            generate_dataset,
            inputs=[schema_output, num_examples, format_str, model],
            outputs=[dataset_output],
        )
        download_button.click(
            download_dataset,
            inputs=[dataset_output, schema_output, theme, format_str],
            outputs=[download_output],
        )
    return demo


if __name__ == "__main__":
    load_dotenv(find_dotenv())
    demo = ui()
    demo.launch(share=False, debug=True)
