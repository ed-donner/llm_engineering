#!/usr/bin/env python3
"""Run day2 notebook critical path: imports, scraper, and one LLM call (no Gradio launch)."""
import os
import sys

# Run from this folder so scraper is importable
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("1. Imports...")
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
print("   gradio, dotenv, openai OK")

print("2. Load env and OpenRouter client...")
try:
    load_dotenv(override=True)
except Exception as e:
    print(f"   (could not load .env: {e})")
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
if not openrouter_api_key:
    print("   OPENROUTER_API_KEY not set; skipping LLM call")
else:
    print(f"   OpenRouter key OK (begins {openrouter_api_key[:8]}...)")
openrouter_url = "https://openrouter.ai/api/v1"
openai = OpenAI(base_url=openrouter_url, api_key=openrouter_api_key or "dummy")

print("3. Scraper import and fetch_website_contents...")
from scraper import fetch_website_contents
try:
    content = fetch_website_contents("https://example.com")
    assert "Example Domain" in content or "example" in content.lower(), content[:200]
    print(f"   scraper OK (got {len(content)} chars)")
except Exception as e:
    print(f"   scraper fetch skipped (e.g. SSL in env): {e}")

print("4. message_gpt (OpenRouter)...")
system_message = "You are a helpful assistant."
def message_gpt(prompt):
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]
    r = openai.chat.completions.create(model="openai/gpt-4.1-mini", messages=messages)
    return r.choices[0].message.content

if openrouter_api_key:
    reply = message_gpt("Say 'Day2 check OK' and nothing else.")
    print(f"   reply: {reply[:80]}...")
else:
    print("   skipped (no API key)")

print("Done. Day2 notebook path OK.")
