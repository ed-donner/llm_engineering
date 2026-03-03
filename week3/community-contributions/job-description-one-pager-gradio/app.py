"""
Job one-pager – Week 3 community contribution.
Tab 1: Paste job URL or text → one-pager.
Tab 2: Describe role → generate synthetic job posting → one-pager from it.
Set OPENROUTER_API_KEY in .env or Space Secrets.
"""
import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

from one_pager import stream_one_pager, stream_synthetic_job_posting

load_dotenv(override=True)

MODELS = [
    ("openai/gpt-4o-mini", "GPT-4o Mini (OpenAI)"),
    ("openai/gpt-4o", "GPT-4o (OpenAI)"),
    ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet (Anthropic)"),
    ("anthropic/claude-3-haiku", "Claude 3 Haiku (Anthropic)"),
    ("google/gemini-2.0-flash-001", "Gemini 2.0 Flash (Google)"),
    ("meta-llama/llama-3.1-70b-instruct", "Llama 3.1 70B (Meta)"),
]
DEFAULT_MODEL_ID = "openai/gpt-4o-mini"


def stream_one_pager_accumulated(url_or_text: str, model_id: str):
    if not url_or_text or not url_or_text.strip():
        yield "Paste a job URL or full job description above, then click Generate."
        return
    acc = ""
    for chunk in stream_one_pager(url_or_text.strip(), model=model_id):
        acc += chunk
        yield acc


def stream_synthetic_job_accumulated(scenario: str, model_id: str):
    if not scenario or not scenario.strip():
        yield "Describe the role above (e.g. Senior backend engineer, fintech, 5+ years Python), then click Generate."
        return
    acc = ""
    for chunk in stream_synthetic_job_posting(scenario.strip(), model=model_id):
        acc += chunk
        yield acc


def save_as_md(content: str) -> str:
    if not content or content.startswith("Error:") or content.startswith("Paste a job") or content.startswith("Describe the role"):
        return "Nothing to save. Generate a one-pager first."
    path = Path.cwd() / "job_one_pager.md"
    try:
        path.write_text(content, encoding="utf-8")
        return f"Saved to {path.name}"
    except Exception as e:
        return f"Save failed: {e} (on Spaces, copy from the textbox instead)"


with gr.Blocks(title="Job one-pager (Week 3)", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # Job posting → one-pager (Week 3)
        **Tab 1:** Paste a job URL or description → one-pager.  
        **Tab 2 (Synthetic data):** Describe a role → generate a **synthetic job posting** → then one-pager from it.
        """
    )
    with gr.Row():
        model_dropdown = gr.Dropdown(
            label="Model",
            choices=[(label, id_) for id_, label in MODELS],
            value=DEFAULT_MODEL_ID,
            allow_custom_value=False,
        )

    with gr.Tabs():
        with gr.Tab("Paste job"):
            url_or_text = gr.Textbox(
                label="Job URL or pasted description",
                placeholder="https://company.com/careers/role  or  Senior Engineer – Backend\nCompany X – Remote...",
                lines=8,
                max_lines=20,
            )
            with gr.Row():
                generate_btn = gr.Button("Generate one-pager", variant="primary")
            output = gr.Textbox(
                label="One-pager (markdown)",
                lines=20,
                max_lines=40,
                show_copy_button=True,
            )
            with gr.Row():
                save_btn = gr.Button("Save as .md")
            status = gr.Textbox(label="Status", interactive=False)
            generate_btn.click(
                fn=stream_one_pager_accumulated,
                inputs=[url_or_text, model_dropdown],
                outputs=output,
            )
            save_btn.click(fn=save_as_md, inputs=output, outputs=status)

        with gr.Tab("Synthetic job (Week 3)"):
            gr.Markdown("Describe the role in a few words; the model generates a realistic fake job ad. Then generate the one-pager from it.")
            scenario = gr.Textbox(
                label="Describe the role",
                placeholder="e.g. Senior backend engineer, fintech, 5+ years Python, remote",
                lines=2,
            )
            with gr.Row():
                gen_job_btn = gr.Button("Generate synthetic job posting", variant="primary")
            synthetic_job_text = gr.Textbox(
                label="Generated job posting",
                lines=12,
                max_lines=25,
                show_copy_button=True,
            )
            with gr.Row():
                gen_onepager_btn = gr.Button("Generate one-pager from this")
            one_pager_tab2 = gr.Textbox(
                label="One-pager (markdown)",
                lines=20,
                max_lines=40,
                show_copy_button=True,
            )
            with gr.Row():
                save_btn_tab2 = gr.Button("Save as .md")
            status_tab2 = gr.Textbox(label="Status", interactive=False)
            gen_job_btn.click(
                fn=stream_synthetic_job_accumulated,
                inputs=[scenario, model_dropdown],
                outputs=synthetic_job_text,
            )
            gen_onepager_btn.click(
                fn=stream_one_pager_accumulated,
                inputs=[synthetic_job_text, model_dropdown],
                outputs=one_pager_tab2,
            )
            save_btn_tab2.click(
                fn=save_as_md,
                inputs=one_pager_tab2,
                outputs=status_tab2,
            )

if __name__ == "__main__":
    demo.launch()
