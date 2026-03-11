"""
Minimal Gradio UI entrypoint that imports Generator and runs locally.
Run: uv run gradio_ui.py
"""

import os
import json
import gradio as gr
from dotenv import load_dotenv

from cursor_synth.core import TemplateRegistry, PromptEngine, HFClient, Validator, Generator

load_dotenv()

HF_MODEL_ID="HuggingFaceTB/SmolLM3-3B:hf-inference" # SmolLM3 via Hugging Face router

registry = TemplateRegistry()
prompt_engine = PromptEngine()
hf_client = HFClient(model_id=HF_MODEL_ID, api_key=os.getenv("HF_API_KEY"))
validator = Validator()
generator = Generator(hf_client, registry, prompt_engine, validator)

def generate_action(template_id: str, count: int, tone: str, temperature: float, max_tokens: int, custom_prompt: str, show_raw: bool):
    params = {"count": count, "tone": tone}
    if template_id == "custom":
        result = generator.generate(None, params, custom_prompt=custom_prompt, temperature=temperature, max_tokens=max_tokens)
    else:
        result = generator.generate(template_id, params, custom_prompt=None, temperature=temperature, max_tokens=max_tokens)
    output = result.get("output")
    raw = result.get("raw_model_text", "")
    validation = result.get("validation", {"valid": False, "errors": []})
    json_text = json.dumps(output, indent=2) if output is not None else ""
    
    # Enhanced debug info to show what type of data we got
    output_type = type(output).__name__
    if isinstance(output, list):
        output_count = len(output)
        debug_info = f"Status: {result.get('status', 'unknown')}\nOutput type: {output_type} (length: {output_count})\nRaw length: {len(raw)} chars\nFirst 200 chars: {raw[:200]}"
    else:
        debug_info = f"Status: {result.get('status', 'unknown')}\nOutput type: {output_type} (single object)\nRaw length: {len(raw)} chars\nFirst 200 chars: {raw[:200]}"
    
    if show_raw:
        return json_text, raw, json.dumps(validation, indent=2)
    return json_text, debug_info, json.dumps(validation, indent=2)

# build UI
templates = registry.get_ids()
templates_dropdown = templates + ["custom"]

with gr.Blocks(title="Cursor Synth - Minimal") as demo:
    with gr.Row():
        with gr.Column(scale=1):
            template = gr.Dropdown(label="Template", choices=templates_dropdown, value=templates_dropdown[0])
            count = gr.Slider(label="Count", minimum=1, maximum=10, value=1, step=1)
            tone = gr.Textbox(label="Tone (optional)", value="concise")
            temperature = gr.Slider(label="Temperature", minimum=0.0, maximum=1.0, value=0.2, step=0.05)
            max_tokens = gr.Number(label="Max tokens", value=512)
            custom_prompt = gr.Textbox(
                label="Custom prompt (used if Template=custom)", 
                lines=6, 
                visible=True, 
                placeholder="Example: Generate 3 social media posts as JSON array. Each post must have: platform, content, hashtags (array), engagement_metrics (object with likes, shares, comments). Tone: engaging. Start with [ and end with ]. No thinking, just JSON.",
                value=""
            )
            show_raw = gr.Checkbox(label="Show raw model output", value=False)
            gen_btn = gr.Button("Generate")
        with gr.Column(scale=1):
            output = gr.Code(label="Output (JSON)", language="json")
            raw_out = gr.Textbox(label="Raw model output", lines=8)
            validation = gr.Code(label="Validation", language="json")

    def on_template_change(t):
        if t == "custom":
            return gr.update(visible=True, label="Custom prompt (ACTIVE - will be used for generation)")
        else:
            return gr.update(visible=True, label="Custom prompt (used if Template=custom)")

    template.change(on_template_change, inputs=[template], outputs=[custom_prompt])

    gen_btn.click(fn=generate_action,
                  inputs=[template, count, tone, temperature, max_tokens, custom_prompt, show_raw],
                  outputs=[output, raw_out, validation])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=int(os.getenv("PORT", 7860)))
