import os
import requests
from IPython.display import Markdown, display, update_display
from openai import OpenAI
from google.colab import drive
from huggingface_hub import login
from google.colab import userdata
from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer, BitsAndBytesConfig, pipeline, TextGenerationPipeline
import torch
from consts import FALCON, MISTRAL, Databricks
from dotenv import load_dotenv
import json
import ast
import gradio as gr
import re

# Sign in to HuggingFace Hub
load_dotenv()
hf_token = os.getenv("HF_TOKEN")


# Main Prompt
prompt = """
Generate one fake job posting for a {{role}}.

Return only a single JSON object with:
- title
- description (5-10 sentences)
- requirements (array of 4-6 strings)
- location
- company_name

No explanations, no extra text.
Only the JSON object.
"""

# Main Conf
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_quant_type="nf4"
)

def load_model_and_tokenizer():
  tokenizer = AutoTokenizer.from_pretrained(MISTRAL, trust_remote_code=True)

  model = AutoModelForCausalLM.from_pretrained(
  MISTRAL,
  device_map={"": "cuda"},
  trust_remote_code=True,
  offload_folder="/tmp/dolly_offload",
  quantization_config=bnb_config
  )

  return model, tokenizer


def generate_job(role="Software Engineer", model=None, tokenizer=None):
    # prompt = prompt.format(role=role, n=n)
    # outputs = generator(prompt, max_new_tokens=500, do_sample=True, temperature=0.9)
    # return outputs[0]['generated_text']
    
    # Apply chat template formatting
    # inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
    inputs = tokenizer(prompt.format(role=role), return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}


    # Generate output
    outputs = model.generate(
        **inputs,
        max_new_tokens=600,
        do_sample=True,
        temperature=0.2,
        top_p=0.9,
        pad_token_id=tokenizer.eos_token_id
    )

    # Decode and return
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return result

def generate_jobs(role="Software Engineer", n=5):
  model, tokenizer = load_model_and_tokenizer()
  role = "Software Engineer"
  fake_jobs = []
  for i in range(n):
      fake_jobs.append(generate_job(role=role, model=model, tokenizer=tokenizer))
  return fake_jobs

def extract_json_objects_from_text_block(texts):
    """
    Accepts either a single string or a list of strings.
    Extracts all valid JSON objects from messy text blocks.
    """
    if isinstance(texts, str):
        texts = [texts]  # wrap in list if single string

    pattern = r"\{[\s\S]*?\}"
    results = []

    for raw_text in texts:
        matches = re.findall(pattern, raw_text)
        for match in matches:
            try:
                obj = json.loads(match)
                results.append(obj)
            except json.JSONDecodeError:
                continue

    return results

def generate_ui(role, n):
    try:
        raw_jobs = generate_jobs(role, n)
        parsed_jobs = extract_json_objects_from_text_block(raw_jobs)

        if not isinstance(parsed_jobs, list) or not all(isinstance(item, dict) for item in parsed_jobs):
            print("[ERROR] Parsed result is not a list of dicts")
            return gr.update(value=[], visible=True), None

        filename = f"data/{role.replace(' ', '_').lower()}_jobs.json"
        with open(filename, "w") as f:
            json.dump(parsed_jobs, f, indent=2)

        print(f"[INFO] Returning {len(parsed_jobs)} jobs -> {filename}")
        return parsed_jobs, filename

    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        return gr.update(value=[], visible=True), None


if __name__ == "__main__":
  with gr.Blocks() as demo:
      gr.Markdown("# 🧠 Synthetic Job Dataset Generator")
      gr.Markdown("Generate a structured dataset of job postings for a specific role.")

      with gr.Row():
          role_input = gr.Textbox(label="Job Role", placeholder="e.g. Software Engineer", value="Software Engineer")
          n_input = gr.Number(label="Number of Samples", value=5, precision=0)

      generate_button = gr.Button("🚀 Generate")
      output_table = gr.JSON(label="Generated Dataset")
      download_button = gr.File(label="Download JSON")

      generate_button.click(
          generate_ui,
          inputs=[role_input, n_input],
          outputs=[output_table, download_button]
      )

  demo.launch(debug=True, share=True)


