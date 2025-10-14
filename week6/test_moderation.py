#!/usr/bin/env python3
"""
Test all training data against OpenAI's moderation API to identify problematic content.
This script will test both the input prompts and the fine-tuned model's potential outputs.
"""

import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
client = OpenAI()

def test_moderation(text, label=""):
    """Test a single text against moderation API"""
    try:
        result = client.moderations.create(input=text)
        mod = result.results[0]

        if mod.flagged:
            print(f"\n{'='*80}")
            print(f"🚨 FLAGGED: {label}")
            print(f"{'='*80}")
            print(f"Text preview: {text[:200]}...")
            print(f"\nCategories flagged:")
            for category, flagged in mod.categories.model_dump().items():
                if flagged:
                    scores = mod.category_scores.model_dump()
                    print(f"  - {category}: {scores.get(category, 0):.4f}")
            return True
        return False
    except Exception as e:
        print(f"Error testing {label}: {e}")
        return False

def test_jsonl_file(filepath):
    """Test all examples in a JSONL file"""
    print(f"\n{'='*80}")
    print(f"Testing file: {filepath}")
    print(f"{'='*80}")

    flagged_count = 0
    total_count = 0
    flagged_items = []

    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                messages = data.get('messages', [])

                # Test each message in the conversation
                for msg in messages:
                    role = msg.get('role', '')
                    content = msg.get('content', '')

                    if test_moderation(content, f"Line {line_num} - {role}"):
                        flagged_count += 1
                        flagged_items.append({
                            'line': line_num,
                            'role': role,
                            'preview': content[:100]
                        })

                total_count += 1

                # Rate limiting - don't overwhelm the API
                time.sleep(0.1)

            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num}: {e}")

    print(f"\n{'='*80}")
    print(f"SUMMARY for {filepath}")
    print(f"{'='*80}")
    print(f"Total examples tested: {total_count}")
    print(f"Flagged examples: {flagged_count}")
    print(f"Clean examples: {total_count - flagged_count}")

    if flagged_items:
        print(f"\n⚠️  FLAGGED ITEMS:")
        for item in flagged_items[:10]:  # Show first 10
            print(f"  Line {item['line']} ({item['role']}): {item['preview']}...")

    return flagged_count, total_count

if __name__ == "__main__":
    print("Testing training and validation data for content moderation issues...")
    print("This will help identify what's causing the fine-tuning job to fail.\n")

    # Test training file
    train_flagged, train_total = test_jsonl_file("fine_tune_train.jsonl")

    # Test validation file
    val_flagged, val_total = test_jsonl_file("fine_tune_validation.jsonl")

    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}")
    print(f"Training: {train_flagged}/{train_total} flagged")
    print(f"Validation: {val_flagged}/{val_total} flagged")
    print(f"Total flagged: {train_flagged + val_flagged}")

    if train_flagged + val_flagged > 0:
        print("\n❌ FAILED: Your data still contains content that triggers moderation.")
        print("   You need to remove these items before fine-tuning.")
    else:
        print("\n✅ PASSED: All content is clean and should pass OpenAI's moderation.")
