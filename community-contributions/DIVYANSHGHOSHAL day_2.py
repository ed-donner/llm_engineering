import requests
from bs4 import BeautifulSoup
import ollama

# 1. Fetch the actual website content (using a cleaner URL as an example)
url = "https://en.wikipedia.org/wiki/Kaggle"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Extract the text and limit it to the first 5000 characters so we don't overload the local model
website_content = soup.get_text(separator=' ', strip=True)[:5000]

# 2. Create your prompts
system_prompt = "You are a senior software engineer at a company that builds AI agents. You are tasked to summarize useful information from a website."

# We inject the scraped text dynamically using an f-string
user_prompt = f"""
    Here is the website content:
    {website_content}
    
    Please summarize the website content in a few sentences.
"""

# 3. Make the messages list
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt}
]

# 4. Call Ollama
# Make sure your Ollama app is running in the background!
print("Thinking...")
response = ollama.chat(
    model="llama3.2:1b", 
    messages=messages
)

# 5. Print the result
print("\n--- Summary ---")
print(response['message']['content'])
