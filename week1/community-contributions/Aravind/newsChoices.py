from dotenv import load_dotenv
from openai import OpenAI
from scraper import fetch_website_contents
import os
import random

# Load .env file
load_dotenv()

# Read API key
api_key = os.getenv("OPENROUTER_API_KEY")

# Create client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

try:
    language = random.choice(["English", "French", "Spanish", "Mexican", "Korean", "Hindi"])  

    # Print response
    print("\n News in Language: " + language)
    print("\n")


    # Call the model
    response = client.chat.completions.create(
        model="openai/gpt-5-nano", #openai/gpt-4o-mini
        messages=[
            {
                "role": "system",
                "content": "In "+language
            },
            {
                "role": "user",
                "content": "Provide a summary this web page data - "+fetch_website_contents("https://www.indiatvnews.com/")
            }            
        ]
    )

    # Print response
    print("\nLLM Response:\n")
    print(response.choices[0].message.content)
 



except Exception as e:
    print("\nError:")
    print(e)