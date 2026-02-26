"""Brochure generation logic (from day5 notebook)."""
import json
import os
from openai import OpenAI

from scraper import fetch_website_links, fetch_website_contents

LINK_SYSTEM_PROMPT = """
You are provided with a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:

{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""

BROCHURE_SYSTEM_PROMPT = """
You are an assistant that analyzes the contents of several relevant pages from a company website
and creates a short brochure about the company for prospective customers, investors and recruits.
Respond in markdown without code blocks.
Include details of company culture, customers and careers/jobs if you have the information.
"""

# Model names: configurable via env (e.g. gpt-4o-mini, gpt-4.1-mini)
LINK_MODEL = os.getenv("OPENAI_LINK_MODEL", "gpt-4o-mini")
BROCHURE_MODEL = os.getenv("OPENAI_BROCHURE_MODEL", "gpt-4o-mini")


def _get_links_user_prompt(url: str) -> str:
    links = fetch_website_links(url)
    user_prompt = f"""
Here is the list of links on the website {url} -
Please decide which of these are relevant web links for a brochure about the company,
respond with the full https URL in JSON format.
Do not include Terms of Service, Privacy, email links.

Links (some might be relative links):

"""
    user_prompt += "\n".join(links)
    return user_prompt


def select_relevant_links(client: OpenAI, url: str) -> dict:
    """Use LLM to select brochure-relevant links from the page."""
    response = client.chat.completions.create(
        model=LINK_MODEL,
        messages=[
            {"role": "system", "content": LINK_SYSTEM_PROMPT},
            {"role": "user", "content": _get_links_user_prompt(url)},
        ],
        response_format={"type": "json_object"},
    )
    result = response.choices[0].message.content
    return json.loads(result)


def fetch_page_and_all_relevant_links(client: OpenAI, url: str) -> str:
    """Fetch landing page and all relevant linked pages content."""
    contents = fetch_website_contents(url)
    relevant_links = select_relevant_links(client, url)
    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
    for link in relevant_links.get("links", []):
        try:
            result += f"\n\n### Link: {link['type']}\n"
            result += fetch_website_contents(link["url"])
        except Exception:
            result += "\n[Content unavailable]\n"
    return result


def get_brochure_user_prompt(client: OpenAI, company_name: str, url: str) -> str:
    """Build the user prompt for brochure generation."""
    user_prompt = f"""
You are looking at a company called: {company_name}
Here are the contents of its landing page and other relevant pages;
use this information to build a short brochure of the company in markdown without code blocks.

"""
    user_prompt += fetch_page_and_all_relevant_links(client, url)
    return user_prompt[:5_000]


def create_brochure(company_name: str, url: str, api_key: str | None = None) -> str:
    """
    Generate a brochure for the company. Uses OPENAI_API_KEY from env if api_key not passed.
    """
    client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    user_prompt = get_brochure_user_prompt(client, company_name, url)
    response = client.chat.completions.create(
        model=BROCHURE_MODEL,
        messages=[
            {"role": "system", "content": BROCHURE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""
