import os
import re
import pickle
import json
from openai import OpenAI
from dotenv import load_dotenv
from testing import Tester

# Load env
load_dotenv(override=True)
openai_api_key = os.getenv('OPENAI_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')
openrouter_api_key = os.getenv('OPENROUTER_API_KEY')

# Clients
gemini = OpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
openrouter = OpenAI(api_key=openrouter_api_key, base_url="https://openrouter.ai/api/v1")

# Load data
with open('test_lite.pkl', 'rb') as file:
    test = pickle.load(file)

# Helper functions
def messages_for(item):
    system_message = "You estimate prices of items. Reply only with the price, no explanation"
    user_prompt = item.test_prompt().replace(" to the nearest dollar","").replace("\n\nPrice is $","")
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": "Price is $"}
    ]

def get_price(s):
    s = s.replace('$','').replace(',','')
    match = re.search(r"[-+]?\d*\.\d+|\d+", s)
    return float(match.group()) if match else 0

# Fixed functions
def run_gemini(item):
    try:
        response = gemini.chat.completions.create(
            model="gemini-1.5-flash", 
            messages=messages_for(item),
            temperature=0,
            max_tokens=10
        )
        reply = response.choices[0].message.content
        return get_price(reply)
    except Exception as e:
        print(f"Gemini Error: {e}")
        return 0

def run_openrouter(item):
    try:
        response = openrouter.chat.completions.create(
            model="gpt-oss-20b:free", 
            messages=messages_for(item),
            temperature=0,
            max_tokens=10,
            extra_headers={
                "HTTP-Referer": "https://localhost", 
                "X-Title": "Local Testing"
            }
        )
        reply = response.choices[0].message.content
        return get_price(reply)
    except Exception as e:
        print(f"OpenRouter Error: {e}")
        return 0

# Run tests (subset to save time/tokens)
print("Testing Gemini...")
Tester.test(run_gemini, test[:5]) 

print("\nTesting OpenRouter...")
Tester.test(run_openrouter, test[:5]) 
