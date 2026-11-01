"""
prompts.py
----------

Central location for every prompt used in the project (system prompts and
user-prompt builder functions). No API calls, scraping, or brochure
assembly logic lives here — only prompt text and prompt construction.
"""

from __future__ import annotations

from scraper import fetch_website_links

# ==========================
# Link-selection prompts
# ==========================

LINK_SYSTEM_PROMPT: str = """
You are provided with a list of links found on a webpage.

Your task is to select the links that are most relevant for creating a professional company brochure.

Select pages such as:
- About or Company
- Products or Services
- Careers or Jobs
- Team or Leadership
- Company History
- Customers or Case Studies
- Press or News
- Important company information

Ignore:
- Terms of Service
- Privacy Policy
- Cookie Policy
- Email links
- Social media profiles
- Unrelated external websites
- Duplicate links
- Navigation or anchor links

IMPORTANT:
- Only select URLs that appear in the provided list.
- Never invent, guess, or modify a URL.
- Do not create URLs that were not provided.
- If there is no suitable page for a category, simply omit it.
- Every selected link must have a valid non-empty URL.

Respond only in JSON using this format:

{
    "links": [
        {
            "type": "about page",
            "url": "https://example.com/about"
        }
    ]
}
"""


def get_links_user_prompt(url: str) -> str:
    """
    Build the user prompt asking the LLM to select relevant links for the
    given website, listing every link extracted from that page.

    :param url: Full URL of the website to inspect.
    :return: The complete user prompt text, including all discovered links.
    """
    user_prompt = f"""
Here is the list of links extracted from the website: {url}

Please identify which links are relevant for creating a professional company brochure.

Select useful pages such as:
- About or Company pages
- Products or Services pages
- Careers or Jobs pages
- Team or Leadership pages
- Company history
- Customers or Case Studies
- Other pages containing important company information

Ignore:
- Terms of Service
- Privacy Policy
- Cookie Policy
- Email links
- Social media profiles
- Unrelated external websites
- Duplicate links
- Navigation or anchor links

Return the selected links as valid JSON with the full HTTPS URL.

Some links may be relative links, so convert them into complete HTTPS URLs using the website domain.

Links:
"""

    links = fetch_website_links(url)
    user_prompt += "\n".join(links)

    return user_prompt


# ==========================
# Brochure-generation prompts
# ==========================

BROCHURE_SYSTEM_PROMPT: str = """
You are an assistant that analyzes the contents of several relevant pages from a company website
and creates a short, professional brochure about the company for prospective customers, investors, and recruits.

Use only the information provided in the website content.
Do not invent facts or make unsupported claims.

Respond in Markdown without code blocks.

Include, when available:
- Company overview
- Products or services
- Company culture
- Customers or use cases
- Team or leadership
- Careers and job opportunities
- Important achievements or differentiators

Keep the brochure clear, concise, professional, and engaging.
"""


def get_brochure_user_prompt(company_name: str, website_content: str) -> str:
    """
    Build the user prompt for brochure generation, given the company name
    and the already-assembled website content (landing page + relevant
    linked pages).

    :param company_name: Name of the company the brochure is about.
    :param website_content: Assembled text content from the company's
        landing page and its relevant linked pages.
    :return: The complete user prompt text to send to the LLM.
    """
    user_prompt = f"""
You are looking at a company called: {company_name}

Here are the contents of its landing page and other relevant pages.

Use this information to build a short, professional company brochure
in Markdown without code blocks.

Use only the information provided below.
Do not invent facts.

Website content:

"""

    user_prompt += website_content

    return user_prompt
