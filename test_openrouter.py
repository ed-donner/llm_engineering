import os
from dotenv import load_dotenv
import requests
import json

# 1. Load your keys
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

def test_connection():
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not found in your .env file!")
        return

    print(f"Checking connection with key: {api_key[:15]}...")
    
    # 2. OpenRouter required headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:3000", 
        "X-Title": "Mark Dev Test",              
        "Content-Type": "application/json"
    }

    # 3. Collect dynamic user input
    user_input = input("👉 What do you want to ask the AI? ")

    # 4. Payload using the dynamic input
    payload = {
        "model": "openai/gpt-4o-mini", 
        "messages": [
            {"role": "user", "content": user_input}
        ]
    }

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload)
    )

    if response.status_code == 200:
        result = response.json()
        print("\n🚀 SUCCESS!")
        print("AI Response:", result['choices'][0]['message']['content'])
    else:
        print(f"\n❌ Failed: {response.status_code}")
        print("Details:", response.text)

if __name__ == "__main__":
    test_connection()
    