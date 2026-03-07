import os
import json
from openai import OpenAI
from datasets import load_dataset
from dotenv import load_dotenv

from week7.get_dataset import BASE_MODEL

load_dotenv(override=True)
openai = OpenAI()

BASE_MODEL = "gpt-4.1-nano-2025-04-14"

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


def fetch_and_format_ats_data(filename, sample_size=600):
    """
    Downloads a public job description dataset from Hugging Face, formats it, 
    and saves it as a JavaScript Object Notation Lines (JSONL) file.
    """
    print(f"Downloading ATS dataset and extracting {sample_size} examples...")
    
    # Load the public dataset of job descriptions
    dataset = load_dataset("jacob-hugging-face/job-descriptions", split="train")
    
    # Shuffle and select a sample for training
    sampled_dataset = dataset.shuffle(seed=42).select(range(sample_size))
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        for row in sampled_dataset:
            # The unstructured text scraped from the career site
            user_content = str(row.get('description', ''))
            
            # The strict JSON structure we want the model to learn to output
            target_json = {
                "core_responsibilities": str(row.get('Core Responsibilities', 'N/A')),
                "required_skills": str(row.get('Required Skills', 'N/A')),
                "educational_requirements": str(row.get('Educational Requirements', 'N/A'))
            }
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": json.dumps(target_json)}
            ]
            
            # Write each conversation as a single stringified JSON line
            f.write(json.dumps({"messages": messages}) + '\n')
            
    print(f"Successfully formatted {sample_size} ATS examples into {filename}")

def run_extraction_fine_tuning():
    train_file_path = "jsonl/ats_extraction_train.jsonl"
    
    # 1. Fetch and format the data
    fetch_and_format_ats_data(train_file_path, sample_size=600)
    
    # 2. Upload the formatted file to OpenAI
    print("Uploading ATS training file to OpenAI...")
    with open(train_file_path, "rb") as f:
        train_file = openai.files.create(file=f, purpose="fine-tune")
    
    print(f"File uploaded successfully. File ID: {train_file.id}")
    
    # 3. Trigger the fine-tuning job
    print("Starting fine-tuning job for JSON extraction...")
    job = openai.fine_tuning.jobs.create(
        training_file=train_file.id,
        model="gpt-4.1-nano-2025-04-14", 
        hyperparameters={"n_epochs": 3}, 
        suffix="ats-json-parser" # Tag the model with a recognizable suffix
    )
    
    print(f"Fine-tuning job successfully submitted! Job ID: {job.id}")

if __name__ == "__main__":
    run_extraction_fine_tuning()