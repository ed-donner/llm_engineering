import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from IPython.display import Markdown, display

# Function to summarize a single website
def summarize(url):
    # Fetch website content
    web_response = requests.get(url)
    soup = BeautifulSoup(web_response.text, 'html.parser')
    text = soup.get_text()
    text = text[:4000]  # limit text size


    # System and user prompts
    system_prompt = "You are a friendly news assistant. Summarize the website in 5 bullet points in very simple words."
    user_prompt = f"""
    This is the content of the website:
    {text}

    Please summarize it in 5 clear bullet points.
    """

    # Prepare messages for the AI
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Connect to Ollama
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    ai_response = client.chat.completions.create(
        model='gemma3:270m',
        messages=messages
    )

    return ai_response.choices[0].message.content

# List of websites to summarize
urls = [
    "https://www.cnn.com",
    "https://www.hindustantimes.com/"
]

# Loop through websites and display summaries
for url in urls:
    print("-----", url, "-----")
    summary = summarize(url)
    display(Markdown(summary))
    print("\n")