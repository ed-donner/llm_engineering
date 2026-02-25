
# sales_brochure_generator.py

from dotenv import load_dotenv
import os
import requests

# Step 0: Load environment variables from .env
load_dotenv()

# Step 1: Get your OpenRouter API key from environment variable
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("Please set your OPENROUTER_API_KEY in environment variables.")

# Step 2: Prepare the function to generate a brochure
def generate_brochure(company_name, company_description):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4.1-mini",   # cheapest OpenRouter model
        "max_tokens": 500,          # limit output size to avoid credit errors
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Create a short, professional sales brochure for this company:\n\n"
                    f"Company Name: {company_name}\n"
                    f"Description: {company_description}\n\n"
                    "Make it engaging, clear, and concise."
                )
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        raise Exception(f"Request failed: {response.status_code}, {response.text}")

# Step 3: Run the generator
if __name__ == "__main__":
    print("=== Sales Brochure Generator ===\n")
    company_name = input("Enter your company name: ").strip()
    company_description = input("Enter your company description: ").strip()
    
    print("\nGenerating brochure...\n")
    try:
        brochure_text = generate_brochure(company_name, company_description)
        print("=== Your Sales Brochure ===\n")
        print(brochure_text)
    except Exception as e:
        print("Error generating brochure:", e)