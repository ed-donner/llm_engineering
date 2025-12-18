import requests
from bs4 import BeautifulSoup
import re
from openai import OpenAI   

openai = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')

headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

class Website:

    def __init__(self, url):
        """
        Create this Website object from the given url using the BeautifulSoup library
        """
        self.url = url
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        self.text = soup.body.get_text(separator="\n", strip=True)
URL = "https://www.geeksforgeeks.org/dsa/tree-data-structure/"


gfg = Website(URL)
#print("Title of the webpage:", gfg.title)
#print("Text content of the webpage:")
#print(gfg.text)

system_prompt = "You are an assistant that analyzes the contents of a website \
and be a study guide, ignoring text that might be navigation related or links to other webpages. \ Make it clear and concise. \The user must understand all the important points from the webpage. \
Respond in markdown."

def user_prompt_for(website):
    user_prompt = f"You are looking at a website titled {website.title}"
    user_prompt += "\nThe contents of this website is as follows; \
please provide a short summary of this website in markdown. \
If it includes news or announcements, then summarize these too.\n\n"
    user_prompt += website.text
    return user_prompt

#print(user_prompt_for(gfg))

def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(website)}
    ]


messages_ = messages_for(gfg)

def study_guide(url):
    website = Website(url)
    response = openai.chat.completions.create(
        model = "deepseek-r1:1.5b",
        messages = messages_
    )
    return response.choices[0].message.content

print(study_guide(URL))