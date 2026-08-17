import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr


def get_llm(local_inference: bool = False):
    load_dotenv(override=True)
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if local_inference:
        return OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )
    else:
        return OpenAI(api_key=openai_api_key)
    

def get_system_prompt():
    return """
    You are a helpful assistant that generates a dataset based on a given schema and example JSON.
    Strictly give the JSON objects in the same format as the example JSON.
    """

def get_user_prompt(example_json: str, schema: str, sample_size: int):
    schema_section = ""
    if schema and schema.strip():
        schema_section = "Use the following schema to generate the JSON objects:\n" + schema
    return f"""
        Generate {sample_size} JSON objects based on the following example JSON:
        {example_json}
        {schema_section}
    """

def generate_dataset(example_json: str, schema: str, local_inference: bool = False, sample_size: int = 5):
    llm = get_llm(local_inference=local_inference)
    model = "gpt-oss:20b" if local_inference else "gpt-4.1-mini"

    response = llm.chat.completions.create(model=model, messages=[
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": get_user_prompt(example_json, schema, int(sample_size))}
    ])
    return response.choices[0].message.content


if __name__ == "__main__":
    with gr.Blocks() as demo:
        gr.Markdown("## Synthetic Dataset Generator (JSON Only)")

        example_data = gr.Textbox(label="Example Data (JSON)", lines=8)
        schema = gr.Textbox(label="Schema", placeholder="Enter schema here")
        local_inference = gr.Checkbox(label="Use local inference", value=False)

        sample_size = gr.Slider(1, 50, value=5, step=1, label="Sample Size")

        output_display = gr.Textbox(label="Generated JSON Output", lines=20)

        generate_btn = gr.Button("Generate Dataset")

        generate_btn.click(
            generate_dataset,
            inputs=[example_data, schema, local_inference, sample_size],
            outputs=[output_display]
        )

        demo.launch()