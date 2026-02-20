import os
from dotenv import load_dotenv
from google import genai

#1. LOAD THE ENVIROMENT VAR FROM .env
load_dotenv()

#2. Get api key
api_key = os.getenv("GEMINI_API_KEY")

#3. Validation check

if not api_key:
    print("Error no API key found")
else:
    print("API key found.")

#5. Initialize the gemini client

client = genai.Client(api_key=api_key)

#4. list models
print("Available models:")
#iterate trough the list of models
for model in client.models.list():
    print(f'-{model.name}')