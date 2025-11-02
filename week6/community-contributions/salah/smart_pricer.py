import sys
import os
sys.path.append("../..")

import pickle
import json
import re
import numpy as np
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from huggingface_hub import login
import matplotlib.pyplot as plt
import math
from typing import List, Tuple, Dict
from dataclasses import dataclass
from collections import defaultdict
import time

load_dotenv(override=True)
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
os.environ['HF_TOKEN'] = os.getenv('HF_TOKEN')

hf_token = os.environ['HF_TOKEN']
login(hf_token, add_to_git_credential=True)

from items import Item
from testing import Tester

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
COLOR_MAP = {"red": RED, "orange": YELLOW, "green": GREEN, "blue": BLUE}


@dataclass
class ConfidentPrediction:
    predicted_price: float
    confidence_score: float
    price_range: Tuple[float, float]
    prediction_details: Dict
    risk_level: str


class SmartPricer:

    def __init__(self, openai_api_key: str = None, fine_tuned_model: str = None):
        self.client = OpenAI(api_key=openai_api_key or os.getenv('OPENAI_API_KEY'))
        self.fine_tuned_model = fine_tuned_model or "gpt-4o-mini-2024-07-18"

        self.prompt_strategies = {
            "direct": self._create_direct_prompt,
            "comparative": self._create_comparative_prompt,
            "detailed": self._create_detailed_prompt,
            "market_based": self._create_market_prompt
        }

        self.price_patterns = [
            r'\$?(\d+\.?\d{0,2})',
            r'(\d+\.?\d{0,2})\s*dollars?',
            r'price.*?(\d+\.?\d{0,2})',
            r'(\d+\.?\d{0,2})\s*USD'
        ]

    def _create_direct_prompt(self, item) -> str:
        description = self._get_clean_description(item)
        return f"""Estimate the price of this product. Respond only with the price number.

Product: {description}

Price: $"""

    def _create_comparative_prompt(self, item) -> str:
        description = self._get_clean_description(item)
        return f"""You are pricing this product compared to similar items in the market.
Consider quality, features, and typical market prices.

Product: {description}

Based on market comparison, the price should be: $"""

    def _create_detailed_prompt(self, item) -> str:
        description = self._get_clean_description(item)
        return f"""Analyze this product and estimate its price by considering:
1. Materials and build quality
2. Brand positioning
3. Features and functionality
4. Target market

Product: {description}

Estimated price: $"""

    def _create_market_prompt(self, item) -> str:
        description = self._get_clean_description(item)
        return f"""As a retail pricing expert, what would this product sell for?
Consider production costs, markup, and consumer willingness to pay.

Product: {description}

Retail price: $"""

    def _get_clean_description(self, item) -> str:
        if hasattr(item, 'test_prompt'):
            prompt = item.test_prompt()
            clean = prompt.replace(" to the nearest dollar", "")
            clean = clean.replace("\n\nPrice is $", "")
            return clean.strip()
        else:
            parts = []
            if 'title' in item:
                parts.append(f"Title: {item['title']}")
            if 'description' in item:
                parts.append(f"Description: {item['description']}")
            if 'features' in item:
                parts.append(f"Features: {item['features']}")
            return '\n'.join(parts)

    def _extract_price(self, response: str) -> float:
        if not response:
            return 0.0

        clean_response = response.replace('$', '').replace(',', '').strip()

        try:
            numbers = re.findall(r'\d+\.?\d{0,2}', clean_response)
            if numbers:
                return float(numbers[0])
        except:
            pass

        return 0.0

    def _get_single_prediction(self, item, strategy_name: str) -> float:
        try:
            prompt_func = self.prompt_strategies[strategy_name]
            prompt = prompt_func(item)

            response = self.client.chat.completions.create(
                model=self.fine_tuned_model,
                messages=[
                    {"role": "system", "content": "You are a product pricing expert. Respond only with a price number."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )

            price = self._extract_price(response.choices[0].message.content)
            return max(0.0, price)

        except Exception as e:
            print(f"Error in {strategy_name} prediction: {e}")
            return 0.0

    def predict_with_confidence(self, item) -> ConfidentPrediction:
        predictions = {}
        for strategy_name in self.prompt_strategies:
            pred = self._get_single_prediction(item, strategy_name)
            if pred > 0:
                predictions[strategy_name] = pred

        if not predictions:
            return ConfidentPrediction(
                predicted_price=50.0,
                confidence_score=0.1,
                price_range=(10.0, 100.0),
                prediction_details={"fallback": 50.0},
                risk_level="high"
            )

        prices = list(predictions.values())
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        min_price = min(prices)
        max_price = max(prices)

        if len(prices) == 1:
            confidence = 0.5
        else:
            coefficient_of_variation = std_price / mean_price if mean_price > 0 else 1.0
            confidence = max(0.1, min(1.0, 1.0 - coefficient_of_variation))

        if confidence > 0.8:
            range_factor = 0.1
        elif confidence > 0.5:
            range_factor = 0.2
        else:
            range_factor = 0.4

        price_range = (
            max(0.5, mean_price * (1 - range_factor)),
            mean_price * (1 + range_factor)
        )

        if confidence > 0.7:
            risk_level = "low"
        elif confidence > 0.4:
            risk_level = "medium"
        else:
            risk_level = "high"

        return ConfidentPrediction(
            predicted_price=mean_price,
            confidence_score=confidence,
            price_range=price_range,
            prediction_details=predictions,
            risk_level=risk_level
        )

    def simple_predict(self, item) -> float:
        confident_pred = self.predict_with_confidence(item)
        return confident_pred.predicted_price


class ConfidenceAwareTester:

    def __init__(self, predictor, data, title="Smart Pricer with Confidence", size=250):
        self.predictor = predictor
        self.data = data
        self.title = title
        self.size = size
        self.results = []
        self.confidence_stats = defaultdict(list)

    def color_for_confidence(self, confidence: float) -> str:
        if confidence > 0.7:
            return "blue"
        elif confidence > 0.4:
            return "green"
        else:
            return "orange"

    def run_enhanced_test(self):
        print(f"\n{self.title}")
        print("=" * 60)

        for i in range(min(self.size, len(self.data))):
            item = self.data[i]

            if hasattr(self.predictor, 'predict_with_confidence'):
                confident_pred = self.predictor.predict_with_confidence(item)
                guess = confident_pred.predicted_price
                confidence = confident_pred.confidence_score
                price_range = confident_pred.price_range
                risk_level = confident_pred.risk_level
            else:
                guess = self.predictor(item)
                confidence = 0.5
                price_range = (guess * 0.8, guess * 1.2)
                risk_level = "medium"

            if hasattr(item, 'price'):
                truth = item.price
                title = item.title[:40] + "..." if len(item.title) > 40 else item.title
            else:
                truth = item.get('price', 0)
                title = item.get('title', 'Unknown')[:40] + "..."

            error = abs(guess - truth)
            in_range = price_range[0] <= truth <= price_range[1]

            self.results.append({
                'guess': guess,
                'truth': truth,
                'error': error,
                'confidence': confidence,
                'in_range': in_range,
                'risk_level': risk_level,
                'title': title
            })

            self.confidence_stats[risk_level].append(error)

            color = self.color_for_confidence(confidence)
            range_indicator = "+" if in_range else "-"

            print(f"{COLOR_MAP[color]}{i+1:3d}: ${guess:6.2f} ({confidence*100:4.1f}%) "
                  f"vs ${truth:6.2f} | Error: ${error:5.2f} | {range_indicator} | {title}{RESET}")

        self._print_confidence_summary()
        self._create_confidence_visualization()

    def _print_confidence_summary(self):
        if not self.results:
            return

        print(f"\nPERFORMANCE SUMMARY")
        print("=" * 60)

        total_predictions = len(self.results)
        avg_confidence = np.mean([r['confidence'] for r in self.results])
        avg_error = np.mean([r['error'] for r in self.results])
        range_accuracy = np.mean([r['in_range'] for r in self.results]) * 100

        print(f"Total Predictions: {total_predictions}")
        print(f"Average Confidence: {avg_confidence:.2f}")
        print(f"Average Error: ${avg_error:.2f}")
        print(f"Range Accuracy: {range_accuracy:.1f}%")

        print(f"\nBY RISK LEVEL:")
        for risk_level in ['low', 'medium', 'high']:
            if risk_level in self.confidence_stats:
                errors = self.confidence_stats[risk_level]
                count = len(errors)
                avg_error = np.mean(errors)
                print(f"  {risk_level.upper():6} risk: {count:3d} predictions, ${avg_error:6.2f} avg error")

        high_conf_results = [r for r in self.results if r['confidence'] > 0.7]
        if high_conf_results:
            high_conf_error = np.mean([r['error'] for r in high_conf_results])
            high_conf_accuracy = np.mean([r['in_range'] for r in high_conf_results]) * 100
            print(f"\nHIGH CONFIDENCE PREDICTIONS (>0.7):")
            print(f"  Count: {len(high_conf_results)}")
            print(f"  Average Error: ${high_conf_error:.2f}")
            print(f"  Range Accuracy: {high_conf_accuracy:.1f}%")

    def _create_confidence_visualization(self):
        if not self.results:
            return

        confidences = [r['confidence'] for r in self.results]
        errors = [r['error'] for r in self.results]

        plt.figure(figsize=(12, 5))

        plt.subplot(1, 2, 1)
        plt.scatter(confidences, errors, alpha=0.6, c=confidences, cmap='RdYlBu')
        plt.xlabel('Confidence Score')
        plt.ylabel('Prediction Error ($)')
        plt.title('Confidence vs Prediction Error')
        plt.colorbar(label='Confidence')

        plt.subplot(1, 2, 2)
        plt.hist(confidences, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        plt.xlabel('Confidence Score')
        plt.ylabel('Count')
        plt.title('Distribution of Confidence Scores')

        plt.tight_layout()
        plt.show()


def create_smart_pricer_function(fine_tuned_model_id: str = None):
    pricer = SmartPricer(fine_tuned_model=fine_tuned_model_id)
    return pricer.simple_predict


def test_smart_pricer_with_confidence(test_data, fine_tuned_model_id: str = None):
    pricer = SmartPricer(fine_tuned_model=fine_tuned_model_id)
    tester = ConfidenceAwareTester(pricer, test_data)
    tester.run_enhanced_test()
    return tester.results


def main():
    print("Smart Product Pricer with Confidence Scoring")
    print("=" * 60)

    try:
        with open('test.pkl', 'rb') as file:
            test_data = pickle.load(file)
        print(f"Loaded {len(test_data)} test items")
    except FileNotFoundError:
        print("Test data not found. Make sure test.pkl is in current directory.")
        return

    pricer = SmartPricer()

    print(f"\nTesting with confidence analysis (50 items)...")
    test_data_sample = test_data[:50]

    tester = ConfidenceAwareTester(pricer, test_data_sample, size=50)
    tester.run_enhanced_test()

    print(f"\nComparison with traditional testing:")
    simple_pricer = create_smart_pricer_function()
    Tester.test(simple_pricer, test_data_sample[:25])


if __name__ == "__main__":
    main()
