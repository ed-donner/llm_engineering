#!/usr/bin/env python3
"""
Comprehensive fix for OpenAI fine-tuning moderation failures.

The issue: OpenAI runs post-training evaluations including 'refusals_v3' which tests
if the fine-tuned model will refuse harmful requests. Product descriptions containing
weapons, tactical gear, or other sensitive content can cause failures.

This script:
1. Loads the original data
2. Tests each item against moderation API
3. Filters out problematic content more aggressively
4. Creates clean JSONL files ready for fine-tuning
"""

import pickle
import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
client = OpenAI()

# Keywords that often trigger moderation issues
SENSITIVE_KEYWORDS = [
    'weapon', 'gun', 'rifle', 'pistol', 'firearm', 'ammunition', 'ammo',
    'knife', 'blade', 'sword', 'dagger', 'tactical', 'combat', 'military',
    'explosive', 'grenade', 'bomb', 'missile', 'assault', 'sniper',
    'hunting knife', 'combat knife', 'self-defense', 'pepper spray',
    'stun gun', 'taser', 'brass knuckles', 'baton', 'throwing knife'
]

def contains_sensitive_content(text):
    """Quick pre-filter for obvious sensitive content"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in SENSITIVE_KEYWORDS)

def test_moderation_api(text):
    """Test content against OpenAI's moderation API"""
    try:
        result = client.moderations.create(input=text)
        return result.results[0].flagged
    except Exception as e:
        print(f"  ⚠️  Moderation API error: {e}")
        return False

def is_safe_for_finetuning(item):
    """
    Comprehensive safety check for fine-tuning.
    Returns True if item is safe, False if it should be filtered.
    """
    # Get the content
    prompt = item.test_prompt().replace(" to the nearest dollar", "").replace("\n\nPrice is $", "")
    full_content = f"How much does this cost?\n\n{prompt}"

    # Quick keyword pre-filter
    if contains_sensitive_content(full_content):
        return False, "sensitive_keywords"

    # Test with moderation API
    if test_moderation_api(full_content):
        return False, "moderation_api"

    # Also test the product name alone (sometimes names are problematic)
    if hasattr(item, 'name') and test_moderation_api(item.name):
        return False, "name_flagged"

    return True, "safe"

def filter_training_data(items, label="data"):
    """Filter items to only include safe content"""
    print(f"\n{'='*80}")
    print(f"Filtering {label}: {len(items)} items")
    print(f"{'='*80}")

    safe_items = []
    filtered_items = []
    filter_reasons = {}

    for idx, item in enumerate(items):
        if (idx + 1) % 20 == 0:
            print(f"  Processed {idx + 1}/{len(items)}...")

        is_safe, reason = is_safe_for_finetuning(item)

        if is_safe:
            safe_items.append(item)
        else:
            filtered_items.append((idx, item, reason))
            filter_reasons[reason] = filter_reasons.get(reason, 0) + 1
            name = getattr(item, 'name', 'Unknown')[:60]
            print(f"  ❌ Filtered item {idx}: {name}... ({reason})")

        # Rate limiting
        time.sleep(0.05)

    print(f"\n{'='*80}")
    print(f"RESULTS for {label}")
    print(f"{'='*80}")
    print(f"✅ Safe items: {len(safe_items)}")
    print(f"❌ Filtered items: {len(filtered_items)}")
    print(f"\nFilter reasons:")
    for reason, count in filter_reasons.items():
        print(f"  - {reason}: {count}")

    return safe_items, filtered_items

def create_messages(item):
    """Create message format for OpenAI fine-tuning"""
    system_message = "You estimate prices of items. Reply only with the price, no explanation"
    user_prompt = item.test_prompt().replace(" to the nearest dollar", "").replace("\n\nPrice is $", "")
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": f"Price is ${item.price:.2f}"}
    ]

def write_jsonl(items, filename):
    """Write items to JSONL format"""
    with open(filename, 'w') as f:
        for item in items:
            messages = create_messages(item)
            json_line = json.dumps({"messages": messages})
            f.write(json_line + '\n')
    print(f"\n✅ Wrote {len(items)} examples to {filename}")

def main():
    print("="*80)
    print("COMPREHENSIVE MODERATION FIX FOR FINE-TUNING")
    print("="*80)

    # Load data
    print("\nLoading training data...")
    with open('train.pkl', 'rb') as f:
        train = pickle.load(f)

    # Split data
    fine_tune_train = train[:200]
    fine_tune_validation = train[200:250]

    print(f"Original training set: {len(fine_tune_train)} items")
    print(f"Original validation set: {len(fine_tune_validation)} items")

    # Filter training data
    safe_train, filtered_train = filter_training_data(fine_tune_train, "TRAINING SET")

    # Filter validation data
    safe_validation, filtered_validation = filter_training_data(fine_tune_validation, "VALIDATION SET")

    # Check if we have enough data
    print(f"\n{'='*80}")
    print("FINAL DATA CHECK")
    print(f"{'='*80}")

    if len(safe_train) < 50:
        print(f"⚠️  WARNING: Only {len(safe_train)} training examples remaining.")
        print("   OpenAI recommends at least 50-100 examples for fine-tuning.")
        print("   Consider using a larger initial dataset.")

    if len(safe_validation) < 10:
        print(f"⚠️  WARNING: Only {len(safe_validation)} validation examples remaining.")

    # Write clean data
    print(f"\nWriting clean JSONL files...")
    write_jsonl(safe_train, "fine_tune_train.jsonl")
    write_jsonl(safe_validation, "fine_tune_validation.jsonl")

    print(f"\n{'='*80}")
    print("✅ DONE! Your data is now ready for fine-tuning.")
    print(f"{'='*80}")
    print(f"\nTraining examples: {len(safe_train)}")
    print(f"Validation examples: {len(safe_validation)}")
    print(f"\nNext steps:")
    print("1. Upload the new JSONL files to OpenAI")
    print("2. Create a new fine-tuning job")
    print("3. The job should now pass moderation checks")

if __name__ == "__main__":
    main()
