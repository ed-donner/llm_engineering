"""
Rayen's lab1 submission (community_contributions)

Instructions:
- This small script demonstrates the prompt and a test call to the Gemini model.
- It expects a `GOOGLE_API_KEY` in your `.env` (or environment).
- This is a .py submission (no notebook outputs). If you prefer a notebook, ask and I'll create one.
"""

import os
from dotenv import load_dotenv

# Use the OpenAI-compatible client for Gemini
from openai import OpenAI

load_dotenv(override=True)
KEY = os.getenv("GOOGLE_API_KEY")
if not KEY:
    raise SystemExit("GOOGLE_API_KEY not set in environment. Add it to .env or export it.")

BASE = "https://generativelanguage.googleapis.com/v1beta/openai/"
client = OpenAI(base_url=BASE, api_key=KEY)
openai = client  # alias for existing notebook code

# Step 1: Create your prompts
system_prompt = "You are a professional code assistant that explains Angular patterns clearly and helps fix bugs."
user_prompt = """
I have an Angular (TypeScript) component that is misbehaving. I suspect the issue is related to state management: the code mixes Angular Signals and RxJS BehaviorSubject, or uses them incorrectly.

Please:
1) Identify likely bugs from the description (I will paste code later if needed).
2) Explain the difference between Angular Signals and RxJS BehaviorSubject, and when to use each.
3) Provide a corrected example or code changes to fix typical bugs when mixing Signals and BehaviorSubject.
4) Give concise best-practice advice for using Signals or BehaviorSubjects in Angular apps (performance, subscriptions, lifecycle, change detection).

Context: my team expects reactive updates and consistent state; I am not confident which primitive to use or how to migrate safely. Help me fix the bug and show step-by-step code changes.
"""

# Step 2: Make the messages list
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt}
]

# Step 3: Call OpenAI (Gemini)
# NOTE: Use an available model for your key. This repo tested with models/gemini-2.5-flash.
TEST_MODEL = "models/gemini-2.5-flash"

response = openai.chat.completions.create(
    model=TEST_MODEL,
    messages=messages
)

# Step 4: print the result
print(response.choices[0].message.content)
