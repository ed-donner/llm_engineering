import sys
import os
sys.path.append("../..")

import json
import pickle
import pandas as pd
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from huggingface_hub import login
from smart_pricer import SmartPricer, ConfidenceAwareTester
import re
from typing import List, Dict, Tuple
import time

load_dotenv(override=True)
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
os.environ['HF_TOKEN'] = os.getenv('HF_TOKEN')

hf_token = os.environ['HF_TOKEN']
login(hf_token, add_to_git_credential=True)

class SmartFineTuner:

    def __init__(self, openai_api_key: str = None):
        self.client = OpenAI(api_key=openai_api_key or os.getenv('OPENAI_API_KEY'))
        self.fine_tuned_model_id = None

        self.training_templates = [
            {
                "system": "You are a product pricing expert. Respond only with the price, no explanation.",
                "user": "Estimate the price of this product:\n\n{description}\n\nPrice: $",
                "weight": 0.4
            },
            {
                "system": "You are a retail pricing expert. Consider market positioning and consumer value.",
                "user": "What would this product sell for in the market?\n\n{description}\n\nMarket price: $",
                "weight": 0.3
            },
            {
                "system": "You analyze product features to determine fair pricing.",
                "user": "Based on the features and quality described, estimate the price:\n\n{description}\n\nEstimated price: $",
                "weight": 0.3
            }
        ]
    
    def prepare_enhanced_training_data(self, train_items: List, template_mix: bool = True) -> List[Dict]:
        training_data = []

        for item in train_items:
            description = self._get_clean_description(item)

            if len(description.strip()) < 20:
                continue

            if hasattr(item, 'price'):
                price = item.price
            else:
                price = item.get('price', 0)

            if price <= 0:
                continue

            templates_to_use = self.training_templates if template_mix else [self.training_templates[0]]

            for template in templates_to_use:
                if template_mix and np.random.random() > template['weight']:
                    continue

                user_prompt = template['user'].format(description=description)

                messages = [
                    {"role": "system", "content": template['system']},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": f"{price:.2f}"}
                ]

                training_data.append({"messages": messages})

        return training_data
    
    def _get_clean_description(self, item) -> str:
        if hasattr(item, 'test_prompt'):
            prompt = item.test_prompt()
            clean = prompt.replace(" to the nearest dollar", "")
            clean = clean.replace("\n\nPrice is $", "")
            clean = re.sub(r'\$\d+\.?\d*', '', clean)
            clean = re.sub(r'\d+\.?\d*\s*dollars?', '', clean)
            return clean.strip()
        else:
            parts = []
            if 'title' in item and item['title']:
                parts.append(f"Title: {item['title']}")
            if 'description' in item and item['description']:
                parts.append(f"Description: {item['description']}")
            if 'features' in item and item['features']:
                parts.append(f"Features: {item['features']}")

            return '\n'.join(parts)
    
    def create_training_files(self, train_items: List, val_items: List,
                            enhanced: bool = True) -> Tuple[str, str]:
        train_data = self.prepare_enhanced_training_data(train_items, template_mix=enhanced)
        val_data = self.prepare_enhanced_training_data(val_items, template_mix=False)

        print(f"Prepared {len(train_data)} training examples")
        print(f"Prepared {len(val_data)} validation examples")

        train_file = "smart_pricer_train.jsonl"
        val_file = "smart_pricer_validation.jsonl"

        with open(train_file, 'w') as f:
            for example in train_data:
                f.write(json.dumps(example) + '\n')

        with open(val_file, 'w') as f:
            for example in val_data:
                f.write(json.dumps(example) + '\n')

        return train_file, val_file
    
    def start_fine_tuning(self, train_file: str, val_file: str,
                         model: str = "gpt-4o-mini-2024-07-18",
                         epochs: int = 1) -> str:
        print(f"Starting fine-tuning with enhanced training data...")

        with open(train_file, 'rb') as f:
            train_file_obj = self.client.files.create(file=f, purpose="fine-tune")

        with open(val_file, 'rb') as f:
            val_file_obj = self.client.files.create(file=f, purpose="fine-tune")

        print(f"Uploaded training file: {train_file_obj.id}")
        print(f"Uploaded validation file: {val_file_obj.id}")

        job = self.client.fine_tuning.jobs.create(
            training_file=train_file_obj.id,
            validation_file=val_file_obj.id,
            model=model,
            hyperparameters={"n_epochs": epochs},
            suffix="smart_pricer"
        )

        self.fine_tuned_model_id = job.id
        print(f"Fine-tuning job created: {job.id}")

        return job.id
    
    def check_job_status(self, job_id: str) -> Dict:
        job = self.client.fine_tuning.jobs.retrieve(job_id)
        return {
            'status': job.status,
            'model': job.fine_tuned_model,
            'created_at': job.created_at,
            'finished_at': job.finished_at
        }
    
    def evaluate_fine_tuned_model(self, test_data: List, job_id: str) -> Dict:
        job_info = self.check_job_status(job_id)

        if job_info['status'] != 'succeeded':
            print(f"Job not completed yet. Status: {job_info['status']}")
            return {}

        fine_tuned_model = job_info['model']
        print(f"Evaluating fine-tuned model: {fine_tuned_model}")

        pricer = SmartPricer(fine_tuned_model=fine_tuned_model)

        tester = ConfidenceAwareTester(
            pricer,
            test_data[:100],
            title=f"Fine-tuned Smart Pricer ({fine_tuned_model})",
            size=100
        )

        results = tester.run_enhanced_test()

        if results:
            avg_error = np.mean([r['error'] for r in results])
            avg_confidence = np.mean([r['confidence'] for r in results])
            high_conf_results = [r for r in results if r['confidence'] > 0.7]
            high_conf_error = np.mean([r['error'] for r in high_conf_results]) if high_conf_results else float('inf')

            summary = {
                'model_id': fine_tuned_model,
                'total_predictions': len(results),
                'average_error': avg_error,
                'average_confidence': avg_confidence,
                'high_confidence_count': len(high_conf_results),
                'high_confidence_error': high_conf_error,
                'job_id': job_id
            }

            print(f"\nEVALUATION SUMMARY:")
            print(f"Average Error: ${avg_error:.2f}")
            print(f"Average Confidence: {avg_confidence:.2f}")
            print(f"High Confidence Predictions: {len(high_conf_results)}")
            print(f"High Confidence Error: ${high_conf_error:.2f}")

            return summary

        return {}

def quick_fine_tune_demo(train_size: int = 200, val_size: int = 50):
    print("Smart Pricer Fine-Tuning Demo")
    print("=" * 50)

    try:
        with open('train.pkl', 'rb') as file:
            train_data = pickle.load(file)
        with open('test.pkl', 'rb') as file:
            test_data = pickle.load(file)
        print(f"Loaded training data: {len(train_data)} items")
        print(f"Loaded test data: {len(test_data)} items")
    except FileNotFoundError:
        print("Training data not found. Make sure train.pkl and test.pkl are in current directory.")
        return

    train_items = train_data[:train_size]
    val_items = train_data[train_size:train_size + val_size]

    print(f"Using {len(train_items)} training items, {len(val_items)} validation items")

    fine_tuner = SmartFineTuner()

    train_file, val_file = fine_tuner.create_training_files(
        train_items, val_items, enhanced=True
    )

    print(f"Created training files: {train_file}, {val_file}")

    print(f"\nTo start fine-tuning, uncomment the following lines:")
    print(f"job_id = fine_tuner.start_fine_tuning('{train_file}', '{val_file}')")
    print(f"# Wait for job to complete...")
    print(f"# results = fine_tuner.evaluate_fine_tuned_model(test_data, job_id)")

    print(f"\nDemo with base model (no fine-tuning):")
    pricer = SmartPricer()
    tester = ConfidenceAwareTester(pricer, test_data[:25], size=25)
    tester.run_enhanced_test()

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Smart Pricer Fine-Tuning')
    parser.add_argument('--demo', action='store_true', help='Run demo mode')
    parser.add_argument('--train-size', type=int, default=200, help='Training set size')
    parser.add_argument('--val-size', type=int, default=50, help='Validation set size')
    parser.add_argument('--evaluate', type=str, help='Evaluate existing model by job ID')

    args = parser.parse_args()

    if args.demo:
        quick_fine_tune_demo(args.train_size, args.val_size)
    elif args.evaluate:
        try:
            with open('test.pkl', 'rb') as file:
                test_data = pickle.load(file)
            fine_tuner = SmartFineTuner()
            fine_tuner.evaluate_fine_tuned_model(test_data, args.evaluate)
        except FileNotFoundError:
            print("Test data not found. Make sure test.pkl is in current directory.")
    else:
        print("Use --demo to run demo or --evaluate <job_id> to evaluate existing model")

if __name__ == "__main__":
    main()