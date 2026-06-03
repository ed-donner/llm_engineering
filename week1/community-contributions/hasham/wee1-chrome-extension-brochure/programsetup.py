import json
import os
from openai import OpenAI
import commonfunctions as cf
from dotenv import load_dotenv


load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')
openai = OpenAI()
Model = "gpt-4.1-mini"

def select_relevant_links(url):
    print(f"Selecting relevant links for {url} by calling {Model}")
    response = openai.chat.completions.create(
        model=Model, 
        messages=[
            {"role": "system", "content": cf.link_system_prompt},
            {"role": "user", "content": cf.get_links_user_prompt(url)},
        ], 
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    links = json.loads(result)
    print(f"Found {len(links['links'])} relevant links")
    return links


def fetch_page_and_all_relevant_links(url):
    contents = cf.fetch_website_contents(url)
    relevant_links = select_relevant_links(url)
    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
    for link in relevant_links['links']:
        result += f"\n\n### Link: {link['type']}\n"
        result += cf.fetch_website_contents(link["url"])
    return result


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
    response = openai.chat.completions.create(
        model=Model,
        messages=[
            {"role": "system", "content": cf.brochure_system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
        ],
    )
    return response.choices[0].message.content