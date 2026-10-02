import os
import json
from scraper import fetch_website_links, fetch_website_contents
from openai import OpenAI


# links = fetch_website_links("https://edwarddonner.com")
# print(f"Found {len(links)} links on the website.")

base_url = os.getenv("DEEPSEEK_URL", "http://localhost:12434/v1/")
model = os.getenv("DEEPSEEK_MODEL", "ai/deepseek-r1-distill-llama:latest")

client = OpenAI(base_url=base_url, api_key="not-needed")

link_system_prompt = """
You are provided with a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:

{
    "links": [
        {
            "type": "about page", 
            "url": "https://full.url/goes/here/about"
        },
        {
            "type": "careers page", 
            "url": "https://another.full.url/careers"
        }
    ]
}
"""


def get_links_user_prompt(url):
    user_prompt = f"""
Here is the list of links on the website {url} -
Please decide which of these are relevant web links for a brochure about the company, 
respond with the full https URL in JSON format.
Do not include Terms of Service, Privacy, email links.

Links (some might be relative links):

"""
    links = fetch_website_links(url)
    user_prompt += "\n".join(links)
    return user_prompt


# content = get_links_user_prompt("https://edwarddonner.com")

# response = client.chat.completions.create(
#     model=model,
#     messages=[
#         {
#             "role": "system",
#             "content": link_system_prompt
#             + "\nReturn only a valid JSON object. Do not use Markdown fences.",
#         },
#         {
#             "role": "user",
#             "content": content,
#         },
#     ],
#     response_format={"type": "json_object"},
# )
# result = response.choices[0].message.content
def select_relevant_links(url):
    assistant_prefill = "{"
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(url)},
            {"role": "assistant", "content": assistant_prefill}
        ],
        response_format={"type": "json_object"},
        stop=["```", "</think>"]
    )
    result = response.choices[0].message.content
    result = result.split("</think>", 1)[0].strip()
    links, _ = json.JSONDecoder().raw_decode(result.lstrip())
    return links
# result = select_relevant_links("https://edwarddonner.com")
# # print the json butifully
# print(json.dumps(result, indent=2))

# result = select_relevant_links("https://huggingface.com")
# print(json.dumps(result, indent=2))

def fetch_page_and_all_relevant_links(url):
    contents = fetch_website_contents(url)
    relevant_links = select_relevant_links(url)
    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
    for link in relevant_links['links']:
        result += f"\n\n### Link: {link['type']}\n"
        result += fetch_website_contents(link["url"])
    return result

# print(fetch_page_and_all_relevant_links("https://huggingface.co"))

brochure_system_prompt = """
You are an assistant that analyzes the contents of several relevant pages from a company website
and creates a short brochure about the company for prospective customers, investors and recruits.
Respond in markdown without code blocks.
Include details of company culture, customers and careers/jobs if you have the information.
"""

def get_brochure_user_prompt(company_name, url):
    user_prompt = f"""
You are looking at a company called: {company_name}
Here are the contents of its landing page and other relevant pages;
use this information to build a short brochure of the company in markdown without code blocks.\n\n
"""
    user_prompt += fetch_page_and_all_relevant_links(url)
    user_prompt = user_prompt[:5_000] # Truncate if more than 5,000 characters
    return user_prompt

def create_brochure(company_name, url):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": brochure_system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
        ],
    )
    result = response.choices[0].message.content
    return result
    
    
def create_brochure_stream(company_name, url):
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": brochure_system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
        ],
        stream=True
    )
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="", flush=True)
    print()
# create_brochure("Edward Donner", "https://edwarddonner.com")
# create_brochure_stream("HuggingFace", "https://huggingface.co")

def translate_brochure(brochure_text, target_language):
    translation_system_prompt = f"""
You are an assistant that translates a brochure about a company into {target_language}.
Respond in markdown without code blocks.
remember, you are printing to a terminal so you'll need to print it from right to left OR simply swap the letters so the user could read RtL

"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": translation_system_prompt},
            {"role": "user", "content": brochure_text}
        ],
        stream=True
    )
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="", flush=True)
    print()

brochure_text = create_brochure("HuggingFace", "https://huggingface.co")
translate_brochure(brochure_text, "Hebrew")