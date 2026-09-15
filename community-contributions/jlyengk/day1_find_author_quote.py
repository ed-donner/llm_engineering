# imports

import os
import requests
from bs4 import BeautifulSoup

from dotenv import load_dotenv
from openai import OpenAI

 
load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

# Check the key

if not api_key:
    print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
elif not api_key.startswith("sk-proj-"):
    print("An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook")
elif api_key.strip() != api_key:
    print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
else:
    print("API key found and looks good so far!")

openai = OpenAI()


system_prompt = (
    "You are a helpful reading assistant.\n\n"
    "Your job is to look at the provided text block and extract exactly ONE quote "
    "written by the author requested by the user.\n\n"
    "Respond in this exact layout:\n"
    "**Author**: [Name]\n"
    "**Quote**: \"[Quote Text]\""
)



def messages_for(scraped_text_chunk):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Scraped text chunk:\n\n{scraped_text_chunk}"}
    ]

def find_author_quote(target_author):
    url = "https://quotes.toscrape.com"
    response = requests.get(url, timeout=10)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    clean_text = " ".join(soup.get_text().split())
    
    scraped_text_chunk = clean_text[:2000]
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Text chunk:\n{scraped_text_chunk}\n\nFind a quote by: {target_author}"}
        ],
        temperature=0.0
    )
    return response.choices[0].message.content



if __name__ == "__main__":
    result = find_author_quote("jane Austen")
    print(result)


