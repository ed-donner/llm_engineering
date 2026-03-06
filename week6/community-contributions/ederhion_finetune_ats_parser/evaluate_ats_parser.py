import json
import pandas as pd
import gradio as gr
import plotly.express as px
from openai import OpenAI
from pydantic import BaseModel
from datasets import load_dataset
from dotenv import load_dotenv

load_dotenv(override=True)
openai = OpenAI()

BASE_MODEL = "gpt-4.1-nano-2025-04-14"
FINE_TUNED_MODEL = "ft:gpt-4.1-nano-2025-04-14:personal:ats-json-parser:DGHESpdj"
JUDGE_MODEL = "gpt-4o"

SYSTEM_PROMPT = """You are an expert Applicant Tracking System (ATS) parser.
Extract the core responsibilities, required skills, and educational requirements exactly as they appear in the following job description.

CRITICAL RULES:
1. Strict Accuracy: Only extract information explicitly stated in the source text. 
2. Zero Hallucination: Do not invent, infer, or assume any skills, responsibilities, or educational requirements. If a field is missing from the text, extract it as "Not specified".
3. Formatting: Return ONLY a valid, strict JSON object matching this exact schema:
{
  "core_responsibilities": "string",
  "required_skills": "string",
  "educational_requirements": "string"
}
Do not include any Markdown formatting, explanations, or arrays."""

class ExtractionScore(BaseModel):
    json_validity: float
    data_accuracy: float
    hallucination_penalty: float
    feedback: str

def get_test_dataset(start_idx=600, end_idx=650):
    """Fetches a fresh 50-row holdout test set from the ATS dataset."""
    print("Fetching holdout test set from Hugging Face...")
    dataset = load_dataset("jacob-hugging-face/job-descriptions", split="train")
    shuffled_dataset = dataset.shuffle(seed=42)
    test_dataset = shuffled_dataset.select(range(start_idx, end_idx))
    return test_dataset

def generate_extraction(job_description: str, model_name: str) -> str:
    """Extracts JSON using the specified model."""
    response = openai.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": job_description}
        ],
        temperature=0 # Absolute zero for deterministic data extraction
    )
    return response.choices[0].message.content.strip()

def score_with_judge(raw_text: str, generated_json: str, target_json: dict) -> ExtractionScore:
    """Uses GPT-4o as a strict judge to evaluate the JSON extraction."""
    judge_prompt = f"""
    You are an expert Data Engineer evaluating an LLM's JSON extraction pipeline.
    Evaluate the Generated JSON against the Target JSON based on the Raw Text.
    Score the following metrics on a scale of 1.0 to 5.0:
    - JSON Validity: Is the output perfectly structured JSON without Markdown or conversational filler? (Score 5.0 if perfect, 1.0 if broken).
    - Data Accuracy: Did the model accurately capture the responsibilities, skills, and education from the raw text?
    - Hallucination Penalty: Score 5.0 if no hallucinations exist. Deduct points heavily if the model invented skills or education not present in the raw text.
    
    Raw Text: {raw_text}
    Target JSON: {json.dumps(target_json)}
    Generated Output: {generated_json}
    """
    
    response = openai.beta.chat.completions.parse(
        model=JUDGE_MODEL,
        messages=[{"role": "system", "content": judge_prompt}],
        response_format=ExtractionScore,
    )
    
    return response.choices[0].message.parsed

def run_evaluations():
    test_dataset = get_test_dataset()
    raw_results = []
    
    print(f"Running A/B extraction evaluation on {len(test_dataset)} holdout test cases...")
    
    models_to_test = [
        {"id": BASE_MODEL, "display_name": "Base Model (GPT-4.1-Nano)"},
        {"id": FINE_TUNED_MODEL, "display_name": "Fine-Tuned Extraction Model"}
    ]
    
    for i, row in enumerate(test_dataset):
        print(f"\n--- Evaluating Job Posting {i+1} ---")
        raw_text = str(row.get('description', ''))
        
        target_json = {
            "core_responsibilities": str(row.get('Core Responsibilities', 'N/A')),
            "required_skills": str(row.get('Required Skills', 'N/A')),
            "educational_requirements": str(row.get('Educational Requirements', 'N/A'))
        }
        
        for model in models_to_test:
            print(f"Testing {model['display_name']}...")
            
            generated_json = generate_extraction(raw_text, model["id"])
            score = score_with_judge(raw_text, generated_json, target_json)
            
            raw_results.extend([
                {"Model": model["display_name"], "Metric": "JSON Validity", "Score": score.json_validity},
                {"Model": model["display_name"], "Metric": "Data Accuracy", "Score": score.data_accuracy},
                {"Model": model["display_name"], "Metric": "Hallucination Control", "Score": score.hallucination_penalty}
            ])

    df = pd.DataFrame(raw_results)
    avg_scores = df.groupby(["Model", "Metric"])["Score"].mean().reset_index()
    
    # Render the grouped Plotly bar chart
    fig = px.bar(
        avg_scores,
        x="Metric",
        y="Score",
        color="Model",
        barmode="group", 
        title="Base vs. Fine-Tuned ATS Extraction Performance",
        range_y=[0, 5],
        text_auto='.2f',
        color_discrete_sequence=["#4c78a8", "#f58518"] 
    )
    
    fig.update_layout(yaxis_title="Average Score (1.0 - 5.0)", template="plotly_white")
    return fig

def build_dashboard():
    theme = gr.themes.Soft(font=["Inter", "system-ui", "sans-serif"])
    
    with gr.Blocks(title="ATS Extraction Dashboard", theme=theme) as ui:
        gr.Markdown("# 📊 ATS Parser: Base vs. Fine-Tuned Model")
        
        with gr.Row():
            eval_button = gr.Button("Run Extraction Evaluation", variant="primary")
            
        with gr.Row():
            score_chart = gr.Plot(label="Evaluation Scores")
            
        eval_button.click(fn=run_evaluations, outputs=[score_chart])
        
    ui.launch(inbrowser=True)

if __name__ == "__main__":
    build_dashboard()