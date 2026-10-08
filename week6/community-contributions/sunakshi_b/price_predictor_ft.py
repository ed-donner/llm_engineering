#!/usr/bin/env python3
"""
Price Predictor Fine-Tuning Pipeline
-----------------------------------
A functional script to fine-tune an older OpenAI model (gpt-3.5-turbo-0125) 
on the 'Electronics' category of the Amazon Reviews dataset to estimate product prices.

Provides a safer '--prepare-only' flag to just generate training datasets without 
immediately spending API credits.
"""

import os
import json
import random
import argparse
from typing import List, Dict, Tuple, Optional

try:
    from dotenv import load_dotenv
except ImportError:
    # Optional graceful fallback
    def load_dotenv(): pass

# Third-party imports
try:
    from datasets import load_dataset
except ImportError:
    print("Please install datasets using 'pip install datasets'")
    exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Please install openai using 'pip install openai'")
    exit(1)


def generate_prompt_messages(title: str, features: List[str], target_price: Optional[float] = None) -> List[Dict[str, str]]:
    """Format the product context as a structured Markdown prompt."""
    
    system_msg = (
        "You are an expert consumer electronics appraiser. Given a generic product "
        "title and its list of features, deduce a highly accurate market price."
    )
    
    feature_bullet_points = "\n".join([f"- {f}" for f in features if isinstance(f, str)]) if features else "No features listed."
    
    user_msg = (
        f"### Product Title\n{title}\n\n"
        f"### Key Features\n{feature_bullet_points}\n\n"
        "Estimate the current retail price in dollars format ($X.XX)."
    )
    
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ]
    
    # If a target price exists, this is training. Otherwise, this is testing/inference.
    if target_price is not None:
        messages.append({"role": "assistant", "content": f"${target_price:.2f}"})
        
    return messages


def acquire_and_clean_dataset(target_size: int = 1000) -> List[List[Dict[str, str]]]:
    """Downloads the 'Electronics' Amazon dataset and filters for valid priced items."""
    print("Downloading HuggingFace McAuley-Lab/Amazon-Reviews-2023 - Electronics...")
    dataset = load_dataset("McAuley-Lab/Amazon-Reviews-2023", "raw_meta_Electronics", split="full", streaming=True, trust_remote_code=True)
    
    training_rows = []
    
    for item in dataset:
        try:
            price = float(item.get("price", 0.0))
            if 0 < price < 5000: # Filter out bogus zero-ranges or excessively expensive industrial items
                title = item.get("title", "Unknown Device")
                features = item.get("features", [])
                
                # We need some context to train a model decently
                if not features or len(title) < 5:
                    continue
                
                msgs = generate_prompt_messages(title, features, price)
                training_rows.append(msgs)
                
                if len(training_rows) >= target_size:
                    break
        except (ValueError, TypeError):
            # Skip items where 'price' fails dict coercion to float
            continue
            
    random.shuffle(training_rows)
    return training_rows


def export_jsonl(filepath: str, dataset: List[List[Dict[str, str]]]):
    """Writes the conversational array directly out to the JSONL path."""
    with open(filepath, 'w', encoding='utf-8') as f:
        for msgs in dataset:
            f.write(json.dumps({"messages": msgs}) + '\n')
            

def run_fine_tuning(client: OpenAI, train_path: str, val_path: str):
    """Executes the OpenAI file upload and training API routine onto gpt-3.5-turbo"""
    print(f"Uploading generic files to OpenAI servers: {train_path}, {val_path}")
    
    with open(train_path, "rb") as t_file:
        t_res = client.files.create(file=t_file, purpose="fine-tune")
    
    with open(val_path, "rb") as v_file:
        v_res = client.files.create(file=v_file, purpose="fine-tune")
        
    print(f"Data uploaded! TrA: {t_res.id} | Val: {v_res.id}")
    
    print("\nTriggering Fine-Tuning Job on 'gpt-3.5-turbo-0125'...")
    try:
        job = client.fine_tuning.jobs.create(
            training_file=t_res.id,
            validation_file=v_res.id,
            model="gpt-3.5-turbo-0125",
            seed=1337,
            hyperparameters={
                "n_epochs": 2
            },
            suffix="electronics-pricer"
        )
        print("="*50)
        print(f"Job Initialized! Track Status Here:\nID: {job.id}")
        print("Note: Run `client.fine_tuning.jobs.retrieve('{}')` to poll via API.".format(job.id))
        print("="*50)
    except Exception as e:
        print(f"Failed to submit Fine Tuning Job. Stack Trace: {e}")


def main():
    parser = argparse.ArgumentParser(description="Electronics Pricing Fine Tuner Pipeline")
    parser.add_argument("--prepare-only", action="store_true", help="Download and parse data but don't invoke OpenAI API costs.")
    parser.add_argument("--dataset-size", type=int, default=800, help="Number of records to extract. Default 800.")
    args = parser.parse_args()
    
    load_dotenv()
    
    client = None
    if not args.prepare_only:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: --prepare-only was false, but no OPENAI_API_KEY detected in env variables.")
            return
        client = OpenAI(api_key=api_key)
        
    print("--- Stage 1: Data Preparation ---")
    data_rows = acquire_and_clean_dataset(args.dataset_size)
    
    if len(data_rows) < 50:
        print("Not enough complete records found to meaningfully train against. Exiting.")
        return
        
    train_split = int(len(data_rows) * 0.8)
    train_data = data_rows[:train_split]
    val_data = data_rows[train_split:]
    
    train_file = "electronics_pricer_train.jsonl"
    val_file = "electronics_pricer_val.jsonl"
    
    export_jsonl(train_file, train_data)
    export_jsonl(val_file, val_data)
    print(f"Successfully generated offline files -> Training Split: {len(train_data)} | Validation Split: {len(val_data)}")
    
    if args.prepare_only:
        print("\nPipeline exited natively without initiating training (due to --prepare-only).")
        return
    else:
        print("\n--- Stage 2: OpenAI Invocation ---")
        run_fine_tuning(client, train_file, val_file)
        

if __name__ == "__main__":
    main()
