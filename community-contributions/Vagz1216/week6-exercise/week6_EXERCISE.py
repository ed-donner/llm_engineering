import os
import re
import json
import random
import time
import sys
from collections import defaultdict
from dotenv import load_dotenv
from huggingface_hub import login
from openai import OpenAI

# ===================================================================
# THE PRICER: CAPSTONE EXERCISE (WEEK 6)
# ===================================================================
# This script improves upon the instructor's Day 5 fine-tuned model by:
# 1. Balanced Sampling: Ensuring the LLM learns about $500 TVs, not just $5 cables.
# 2. Expert Persona: Engineering a domain-specific prompt for the AI.

# -------------------------------------------------------------------
# STEP 0: SETUP AND IMPORTS
# -------------------------------------------------------------------
# Load the .env file from the root
load_dotenv(override=True)

# Add the week6 folder to the Python path so we can import the instructor's custom classes
sys.path.append(os.path.abspath("../../../week6"))
try:
    from pricer.items import Item
    from pricer.evaluator import evaluate, Tester
except ImportError:
    print("Warning: Could not import pricer modules. Make sure you are running this from the community-contributions folder.")

# Initialize clients
openai = OpenAI()
hf_token = os.environ.get('HF_TOKEN')
if hf_token:
    login(hf_token, add_to_git_credential=True)
else:
    print("WARNING: HF_TOKEN not found in .env")

# -------------------------------------------------------------------
# STEP 1: LOAD THE LITE DATASET
# -------------------------------------------------------------------
print("\n--- STEP 1: Loading Dataset ---")
# We explicitly "borrow" the perfectly cleaned Day 1 data from HuggingFace
username = "ed-donner"
dataset_name = f"{username}/items_lite"

# test=~1000 items, val=~1000 items, train=~20000 items
train, val, test = Item.from_hub(dataset_name)
print(f"Loaded {len(train):,} training items, {len(val):,} validation items, {len(test):,} test items")


# -------------------------------------------------------------------
# STEP 2: THE FIRST IMPROVEMENT - BALANCED SAMPLING
# -------------------------------------------------------------------
# In Day 5, the instructor just sliced the first 100 items: train[:100]
# The Flaw: If the first 100 items are all cheap phone cases, the model
# never learns what an expensive item looks like.
# The Fix: We categorize prices into buckets, and pull equally from each bucket.

def categorize_price(price):
    if price < 50:
        return '$0-50'
    elif price < 150:
        return '$50-150'
    elif price < 300:
        return '$150-300'
    else:
        return '$300+'

print("\n--- STEP 2: Creating Balanced Training Data ---")
# Group items into buckets
price_buckets = defaultdict(list)
for item in train:
    bucket = categorize_price(item.price)
    price_buckets[bucket].append(item)

# We want 500 items for fine-tuning. Since we have 4 buckets, we take 125 from each.
ITEMS_PER_BUCKET = 125 
fine_tune_train = []
random.seed(42)

for bucket, items_in_bucket in price_buckets.items():
    # Randomly select items from this bucket (or as many as there are)
    sample_size = min(ITEMS_PER_BUCKET, len(items_in_bucket))
    sample = random.sample(items_in_bucket, sample_size)
    fine_tune_train.extend(sample)

# Shuffle them so they aren't grouped perfectly by price during training
random.shuffle(fine_tune_train)

# We will take 50 random items for the validation set
fine_tune_validation = random.sample(val, 50)

print(f"Created a balanced training set of {len(fine_tune_train)} items.")
for bucket in sorted(price_buckets.keys()):
    count = sum(1 for x in fine_tune_train if categorize_price(x.price) == bucket)
    print(f" - {bucket} bucket: {count} items")


# -------------------------------------------------------------------
# STEP 3: THE SECOND IMPROVEMENT - EXPERT PERSONA
# -------------------------------------------------------------------
# In Day 5, the prompt was basic: "You estimate prices of items. Reply only with the price..."
# The Fix: We upgrade the System Prompt to an "Expert Persona" with domain context.

EXPERT_SYSTEM_PROMPT = """You are a senior pricing analyst with deep expertise in consumer electronics, appliances, and retail goods.
Analyze the brand, product specifications, and features to estimate the most likely retail market price in USD.
Respond ONLY with the format: Price is $XX.XX"""

def messages_for(item):
    """Creates the 'Flashcard' for the LLM. Front = Description, Back = Price"""
    # Clean up the instructor's messy test_prompt
    user_prompt = item.test_prompt().replace(" to the nearest dollar", "").replace("\n\nPrice is $", "")
    return [
        {"role": "system", "content": EXPERT_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": f"Price is ${item.price:.2f}"} # The answer on the back
    ]


# -------------------------------------------------------------------
# STEP 4: FORMAT AND SAVE JSONL FILES
# -------------------------------------------------------------------
print("\n--- STEP 4: Saving format for Fine-Tuning ---")
def make_jsonl(items):
    result = ""
    for item in items:
        # Convert the dictionary into a JSON string
        result += '{"messages": ' + json.dumps(messages_for(item)) + '}\n'
    return result.strip()

def write_local(items, filename):
    # Write the file locally
    with open(filename, "w") as f:
        f.write(make_jsonl(items))
    return os.path.abspath(filename)

train_path = write_local(fine_tune_train, "fine_tune_train.jsonl")
val_path = write_local(fine_tune_validation, "fine_tune_validation.jsonl")

print(f"✅ Successfully wrote structured training data to:\n -> {train_path}")
print(f"✅ Successfully wrote structured validation data to:\n -> {val_path}")

# -------------------------------------------------------------------
# THE INSTRUCTOR'S NEXT STEPS (Without an OpenAI Key)
# -------------------------------------------------------------------
print("\n🔥 CAPSTONE EXERCISE COMPLETE (DATA ENGINEERING PHASE) 🔥")
print("\nBecause you do not have an OpenAI API key, the automated upload")
print("and training steps in Python have been paused.")
print("\nWhat happens now in terms of the instructor's requirements?")
print("1. COMPLETED: You have proven you can pull raw data and balance it mathematically.")
print("2. COMPLETED: You engineered an 'Expert Persona' to improve LLM accuracy.")
print("3. COMPLETED: You successfully generated standard JSONL fine-tuning flashcards.")
print("\nTo finish the actual 'Fine-Tuning' phase for free:")
print(" - Go to: https://aistudio.google.com/")
print(" - Click 'Create New Tuned Model' in the left menu.")
print(" - Upload the `fine_tune_train.jsonl` file we just created.")
print(" - Let Google train your custom Gemini model for free!")

