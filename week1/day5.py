import ollama
import os
import requests
import json

from bs4 import BeautifulSoup
from IPython.display import Markdown, display

"""
Available Models:
llama3.3:latest                                     a6eb4748fd29    42 GB     24 hours ago
granite3-moe:3b                                     157f538ae66e    2.1 GB    2 weeks ago
granite3-dense:8b                                   199456d876ee    4.9 GB    2 weeks ago
nemotron:70b-instruct-q5_K_M                        def2cefbe818    49 GB     6 weeks ago
llama3.2:3b-instruct-q8_0                           e410b836fe61    3.4 GB    7 weeks ago
llama3.2:latest                                     a80c4f17acd5    2.0 GB    2 months ago
reflection:latest                                   5084e77c1e10    39 GB     3 months ago
HammerAI/llama-3.1-storm:latest                     876631929cf6    8.5 GB    3 months ago
granite-code:34b                                    4ce00960ca84    19 GB     3 months ago
llama3.1:8b                                         91ab477bec9d    4.7 GB    3 months ago
llama3.1-Q8-8b:latest                               3d41179680d6    8.5 GB    3 months ago
nomic-embed-text:latest                             0a109f422b47    274 MB    3 months ago
rjmalagon/gte-qwen2-7b-instruct-embed-f16:latest    a94ce5b37c1c    15 GB     3 months ago
llama3:70b-instruct-q5_K_M                          4e84a5514862    49 GB     3 months ago
llama3:8b                                           365c0bd3c000    4.7 GB    3 months ago
mistral-nemo:12b-instruct-2407-q8_0                 b91eec34730f    13 GB     3 months ago
"""

MODEL = "llama3.3"

messages = [
    {"role": "user", "content": "Describe some of the business applications of Generative AI"}
]

# response = ollama.chat(model=MODEL, messages=messages)
# print(response['message']['content'])
class Website:
    """
    A utility class to represent a website that we have scraped, now with links
    """
    url: str
    title: str
    body: str
    links: list[str]
    text: str

    def __init__(self, url):
        self.url = url
        response = requests.get(url)
        self.body = response.content
        soup = BeautifulSoup(self.body, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        if soup.body:
            try:
                for irrelevant in soup.body(["script", "style", "img", "input"]):
                    irrelevant.decompose()
                self.text = soup.body.get_text(separator="\n", strip=True)
            except:
                pass
        else:
            self.text = ""
        links = [link.get('href') for link in soup.find_all('a')]
        self.links = [link for link in links if link]

    def get_contents(self):
        return f"Webpage Title:\n{self.title}\nWebpage Contents:\n{self.text}\n\n"
    
link_system_prompt = "You are provided with a list of links found on a webpage. \
You are able to decide which of the links would be most relevant to include in a brochure about the company, \
such as links to an About page, or a Company page, or Careers/Jobs pages.\n"
link_system_prompt += "You should respond in JSON as in this example:"
link_system_prompt += """
{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page": "url": "https://another.full.url/careers"}
    ]
}
"""

def get_links_user_prompt(website):
    user_prompt = f"Here is the list of links on the website of {website.url} - "
    user_prompt += "please decide which of these are relevant web links for a brochure about the company, respond with the full https URL in JSON format. \
        Do not include Terms of Service, Privacy, email links.\n"
    user_prompt += "Links (some might be relative links):\n"
    user_prompt += "\n".join(website.links)
    return user_prompt

def get_links(url):
    website = Website(url)
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(website)}
      ],
        format="json"
    )
    result = response['message']['content']
    return json.loads(result)

def get_all_details(url):
    result = "Landing page:\n"
    result += Website(url).get_contents()
    links = get_links(url)
    # print("Found links:", links)
    for link in links["links"]:
        result += f"\n\n{link['type']}\n"
        result += Website(link["url"]).get_contents()
    return result

system_prompt = "You are an assistant that analyzes the contents of several relevant pages from a company website \
and creates a short professional sales brochure about the company for prospective customers, investors and recruits. Respond \
in markdown. Include details of company culture, customers and careers/jobs if you have the information."

def get_brochure_user_prompt(company_name, url):
    user_prompt = f"You are looking at a company called: {company_name}\n"
    user_prompt += f"Here are the contents of its landing page and other relevant pages; use this information to build a short brochure of the company in markdown.\n"
    user_prompt += get_all_details(url)
    user_prompt = user_prompt[:20000] # Truncate if more than 5,000 characters
    return user_prompt

def create_brochure(company_name, url):
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
          ],
    )
    result = response['message']['content']
    print(result)

create_brochure("Anthropic", "https://anthropic.com")
