#!/usr/bin/env python3

import os
import json
import random
import math
import re
import pickle
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI
from huggingface_hub import login
from datasets import load_dataset
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

load_dotenv()

os.environ['HF_TOKEN'] = os.getenv('HF_TOKEN', 'your-key-if-not-using-env')

hf_token = os.environ['HF_TOKEN']
if hf_token and hf_token != 'your-key-if-not-using-env':
    login(hf_token, add_to_git_credential=True)
    print("Logged in to Hugging Face")

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

from items import Item
from testing import Tester
print("Successfully imported Item and Tester classes")

class PricePredictionFineTuner:
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.train = []
        self.test = []
        self.fine_tune_train = []
        self.fine_tune_validation = []
        self.fine_tuned_model_name = None
        self.wandb_integration = {"type": "wandb", "wandb": {"project": "gpt-pricer"}}
        
    def load_amazon_data(self, category: str = "Appliances") -> None:
        print(f"Loading Amazon Reviews 2023 dataset - {category} category...")
        
        train_pkl = os.path.join('..', '..', 'train.pkl')
        test_pkl = os.path.join('..', '..', 'test.pkl')
        
        if os.path.exists(train_pkl) and os.path.exists(test_pkl):
            print("Found existing pickle files, loading...")
            with open(train_pkl, 'rb') as file:
                self.train = pickle.load(file)
            
            with open(test_pkl, 'rb') as file:
                self.test = pickle.load(file)
            
            print(f"Loaded {len(self.train)} training items and {len(self.test)} test items from pickle files")
        else:
            print("Pickle files not found. Loading from Hugging Face...")
            self._load_from_huggingface(category)
        
        self.fine_tune_train = self.train[:750]
        self.fine_tune_validation = self.train[750:850]
        
        print(f"Fine-tuning split: {len(self.fine_tune_train)} train, {len(self.fine_tune_validation)} validation")
    
    def _load_from_huggingface(self, category: str) -> None:
        try:
            print(f"Downloading {category} dataset from Hugging Face...")
            dataset = load_dataset("McAuley-Lab/Amazon-Reviews-2023", f"raw_meta_{category}", split="full", trust_remote_code=True)
            
            print(f"Number of {category}: {len(dataset):,}")
            
            print("Processing items with prices...")
            items = []
            processed = 0
            
            for datapoint in dataset:
                try:
                    price = float(datapoint["price"])
                    if price > 0 and price <= 999:
                        item = Item(datapoint, price)
                        if item.include:
                            items.append(item)
                        
                        processed += 1
                        if processed % 1000 == 0:
                            print(f"Processed {processed:,} items, found {len(items):,} valid items")
                            
                        if len(items) >= 2000:
                            print(f"Collected {len(items)} items, stopping for efficiency")
                            break
                            
                except (ValueError, TypeError):
                    continue
            
            print(f"Created {len(items):,} valid Item objects")
            
            if len(items) < 850:
                raise ValueError(f"Not enough valid items found: {len(items)}. Need at least 850.")
            
            random.shuffle(items)
            
            split_point = int(0.8 * len(items))
            self.train = items[:split_point]
            self.test = items[split_point:]
            
            print(f"Split into {len(self.train)} training and {len(self.test)} test items")
            
            print("Saving to pickle files for future use...")
            with open(os.path.join('..', '..', 'train.pkl'), 'wb') as f:
                pickle.dump(self.train, f)
            with open(os.path.join('..', '..', 'test.pkl'), 'wb') as f:
                pickle.dump(self.test, f)
            print("Saved pickle files")
            
        except Exception as e:
            print(f"Error loading from Hugging Face: {e}")
            print("This might be due to:")
            print("1. Missing HF_TOKEN environment variable")
            print("2. Need to accept Meta's terms for the tokenizer")
            print("3. Network connectivity issues")
            raise
    
    
    def messages_for(self, item: Item) -> List[Dict[str, str]]:
        system_message = "You are a price estimation expert. You MUST provide a price estimate for any product described, based on the product details provided. Always respond with '$X.XX' format where X.XX is your best estimate. Never refuse to estimate. Never apologize. Never say you cannot determine the price. Make your best educated guess based on the product description, features, and market knowledge. and as said only reply with the cost nothing else no more comments or words from you just the cost"
        user_prompt = item.test_prompt().replace(" to the nearest dollar", "").replace("\n\nPrice is $", "")
        
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": f"Price is ${item.price:.2f}"}
        ]
    
    def messages_for_testing(self, item: Item) -> List[Dict[str, str]]:
        system_message = "You are a price estimation expert. You MUST provide a price estimate for any product described, based on the product details provided. Always respond with '$X.XX' format where $X.XX is your best estimate. Never refuse to estimate. Never apologize. Never say you cannot determine the price. Make your best educated guess based on the product description, features, and market knowledge. and as said only reply with the cost nothing else no more comments or words from you just the cost"
        user_prompt = item.test_prompt().replace(" to the nearest dollar", "").replace("\n\nPrice is $", "")
        
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": "Price is $"}
        ]
    
    def make_jsonl(self, items: List[Item]) -> str:
        result = ""
        for item in items:
            messages = self.messages_for(item)
            messages_str = json.dumps(messages)
            result += '{"messages": ' + messages_str + '}\n'
        return result.strip()
    
    def write_jsonl(self, items: List[Item], filename: str) -> None:
        with open(filename, "w") as f:
            jsonl = self.make_jsonl(items)
            f.write(jsonl)
    
    def save_training_files(self) -> tuple:
        print("Creating JSONL files...")
        
        self.write_jsonl(self.fine_tune_train, "fine_tune_train.jsonl")
        self.write_jsonl(self.fine_tune_validation, "fine_tune_validation.jsonl")
        
        print("Uploading files to OpenAI...")
        
        with open("fine_tune_train.jsonl", "rb") as f:
            train_file = self.client.files.create(file=f, purpose="fine-tune")
        
        with open("fine_tune_validation.jsonl", "rb") as f:
            validation_file = self.client.files.create(file=f, purpose="fine-tune")
        
        print(f"Files uploaded: {train_file.id}, {validation_file.id}")
        return train_file.id, validation_file.id
    
    def start_fine_tuning(self, train_file_id: str, validation_file_id: str) -> str:
        print("Starting fine-tuning job with Weights and Biases integration...")
        
        wandb_key = os.getenv('WANDB_API_KEY')
        integrations = []
        
        if wandb_key:
            integrations = [self.wandb_integration]
            print("Weights and Biases integration enabled")
        else:
            print("WANDB_API_KEY not found - proceeding without W&B integration")
        
        try:
            job = self.client.fine_tuning.jobs.create(
                training_file=train_file_id,
                validation_file=validation_file_id,
                model="gpt-4o-mini-2024-07-18",
                seed=42,
                hyperparameters={
                    "n_epochs": 1,
                    "learning_rate_multiplier": 0.5,
                    "batch_size": 8
                },
                integrations=integrations,
                suffix="pricer-v2"
            )
            
            print(f"Fine-tuning job started: {job.id}")
            return job.id
                
        except Exception as e:
            print(f"Failed to start fine-tuning job: {e}")
            raise
    
    def monitor_training(self, job_id: str) -> Optional[str]:
        while True:
            job = self.client.fine_tuning.jobs.retrieve(job_id)
            status = job.status
            
            print(f"Status: {status}")
            
            if status == "succeeded":
                model_name = job.fine_tuned_model
                print(f"Training completed! Model: {model_name}")
                return model_name
            elif status == "failed":
                print(f"Training failed: {job.error}")
                return None
            elif status in ["running", "validating_files", "queued"]:
                print(f"Training in progress... ({status})")
                import time
                time.sleep(30)
                continue
            else:
                print(f"Unknown status: {status}")
                import time
                time.sleep(30)
                continue
    
    def get_price(self, s: str) -> float:
        s = s.replace('$', '').replace(',', '')
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0
    
    def gpt_fine_tuned(self, item: Item) -> float:
        if not self.fine_tuned_model_name:
            raise ValueError("No fine-tuned model available")
        
        try:
            response = self.client.chat.completions.create(
                model=self.fine_tuned_model_name,
                messages=self.messages_for_testing(item),
                seed=42,
                max_tokens=7
            )
            reply = response.choices[0].message.content
            return self.get_price(reply)
        except Exception as e:
            print(f"Prediction error: {e}")
            return 0.0
    
    def evaluate_model(self, job_id: str) -> Dict[str, Any]:
        try:
            job = self.client.fine_tuning.jobs.retrieve(job_id)
            self.fine_tuned_model_name = job.fine_tuned_model
            
            if not self.test:
                return {"error": "No test items available"}
            
            test_subset = self.test[:min(250, len(self.test))]
            actual_size = len(test_subset)
            
            print(f"Testing individual prediction first...")
            print(f"Actual price: ${test_subset[0].price}")
            predicted_price = self.gpt_fine_tuned(test_subset[0])
            print(f"Predicted price: ${predicted_price}")
            
            print(f"Test prompt used:")
            print(test_subset[0].test_prompt())
            
            print(f"\nRunning full evaluation with {actual_size} test items...")
            
            test_subset2 = self.test[:actual_size]
            tester = Tester(self.gpt_fine_tuned, test_subset2, size=actual_size)
            tester.run()
            
            return {
                "status": "completed",
                "message": "Evaluation completed using Tester class with RMSLE metrics",
                "test_items": actual_size,
                "model_name": self.fine_tuned_model_name
            }
        except Exception as e:
            return {"error": f"Evaluation failed: {e}"}
    
    def evaluate_existing_model(self, model_name: str) -> Dict[str, Any]:
        print("Evaluating existing fine-tuned model...")
        
        self.fine_tuned_model_name = model_name
        
        if not self.test:
            return {"error": "No test items available. Load data first."}
        
        print(f"Fine-tuned model: {self.fine_tuned_model_name}")
        
        test_subset = self.test[:min(250, len(self.test))]
        actual_size = len(test_subset)
        
        print(f"Testing individual prediction first...")
        print(f"Actual price: ${test_subset[0].price}")
        predicted_price = self.gpt_fine_tuned(test_subset[0])
        print(f"Predicted price: ${predicted_price}")
        
        print(f"Test prompt used:")
        print(test_subset[0].test_prompt())
        
        print(f"\nRunning full evaluation with {actual_size} test items...")
        
        test_subset2 = self.test[:actual_size]
        tester = Tester(self.gpt_fine_tuned, test_subset2, size=actual_size)
        tester.run()
        
        return {
            "status": "completed",
            "message": "Evaluation completed using Tester class with RMSLE metrics",
            "test_items": actual_size,
            "model_name": self.fine_tuned_model_name
        }
    
    def add_wandb_sync(self, job_id: str) -> None:
        try:
            import wandb
            from wandb.integration.openai.fine_tuning import WandbLogger
            
            wandb_key = os.getenv('WANDB_API_KEY')
            if not wandb_key:
                print("WANDB_API_KEY not found - skipping W&B sync")
                return
            
            print("Setting up Weights and Biases monitoring...")
            wandb.login()
            WandbLogger.sync(fine_tune_job_id=job_id, project="gpt-pricer")
            print("Weights and Biases sync enabled")
            
        except ImportError:
            print("wandb not installed - skipping W&B sync")
        except Exception as e:
            print(f"W&B sync failed: {e}")

def main():
    print("Starting Price Prediction Fine-Tuning Process")
    print("Based on reference implementation from day5.ipynb")
    print("=" * 60)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("OPENAI_API_KEY not found in environment")
        print("Set your API key: export OPENAI_API_KEY='your-key-here'")
        return
    
    try:
        fine_tuner = PricePredictionFineTuner(api_key)
        
        print("\nStep 1: Loading Amazon Reviews 2023 dataset...")
        fine_tuner.load_amazon_data("Appliances")
        
        if not fine_tuner.fine_tune_train:
            print("No training data available!")
            return
        
        print("\nStep 2: Creating JSONL files and uploading...")
        train_file_id, validation_file_id = fine_tuner.save_training_files()
        
        print("\nStep 3: Starting fine-tuning job...")
        job_id = fine_tuner.start_fine_tuning(train_file_id, validation_file_id)
        
        print("\nStep 4: Setting up Weights and Biases monitoring...")
        fine_tuner.add_wandb_sync(job_id)
        
        print("\nStep 5: Monitoring training progress...")
        print("This may take several minutes to hours depending on data size...")
        model_name = fine_tuner.monitor_training(job_id)
        
        if model_name:
            print(f"\nFine-tuning completed! Model: {model_name}")
            
            print("\nStep 6: Evaluating model with Tester class...")
            results = fine_tuner.evaluate_model(job_id)
            
            if "error" in results:
                print(f"Evaluation failed: {results['error']}")
            else:
                print(f"{results['message']}")
                print(f"Evaluation used {results['test_items']} test items")
                print("\nCheck the generated chart for detailed RMSLE metrics!")
            
            print("\nPrice prediction fine-tuning process completed!")
            print("  Uses pickle files (train.pkl, test.pkl)")
            print("  750 training examples, 100 validation examples")
            print("  1 epoch")
            print("  Learning rate: 0.5")
            print("  Batch size: 8")
            print("  Assertive system prompt")
            print("  Proper RMSLE evaluation using Tester class")
            print("  Weights and Biases integration")
            
        else:
            print("\nFine-tuning failed - check the error messages above")
            
    except Exception as e:
        print(f"\nError during fine-tuning process: {e}")
        import traceback
        traceback.print_exc()

def evaluate_only(model_name: str):
    print("=" * 60)
    print("EVALUATING EXISTING FINE-TUNED MODEL")
    print("=" * 60)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("OPENAI_API_KEY not found in environment")
        return
    
    try:
        fine_tuner = PricePredictionFineTuner(api_key)
        
        print("\nLoading data...")
        fine_tuner.load_amazon_data("Appliances")
        
        print("\nRunning evaluation...")
        results = fine_tuner.evaluate_existing_model(model_name)
        
        if "error" in results:
            print(f"Evaluation failed: {results['error']}")
        else:
            print(f"\n{results['message']}")
            print(f"Evaluation used {results['test_items']} test items")
            print("\nCheck the generated chart for detailed RMSLE metrics!")
            
    except Exception as e:
        print(f"\nError during evaluation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--evaluate":
        if len(sys.argv) < 3:
            print("Usage: python w6d5.py --evaluate <model_name>")
            print("\nExample:")
            print("  python w6d5.py --evaluate ft:gpt-4o-mini-2024-07-18:techxelo:pricer-improved:CVIfbqic")
        else:
            model_name = sys.argv[2]
            evaluate_only(model_name)
    else:
        main()