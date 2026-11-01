"""
brochure.py
-----------

Responsible only for:

* assembling company information (landing page + relevant linked pages)
* creating the brochure prompt (delegated to prompts.py)
* generating the brochure
* streaming the brochure generation

No scraping mechanics or prompt text definitions live here.
"""

from __future__ import annotations

from links import select_relevant_links
from llm import MODEL, ollama_client
from prompts import BROCHURE_SYSTEM_PROMPT, get_brochure_user_prompt
from scraper import fetch_website_contents
from utils import truncate_text

# Same limit used in the original notebook when building the brochure prompt.
MAX_BROCHURE_PROMPT_CHARACTERS: int = 5_000


def fetch_page_and_all_relevant_links(url: str) -> str:
    """
    Scrape a company's landing page plus every relevant linked page
    selected by the LLM, and combine them into a single block of text.

    :param url: Full URL of the company's landing page.
    :return: Combined text of the landing page and successfully fetched
        relevant linked pages.
    """
    contents = fetch_website_contents(url)
    relevant_links = select_relevant_links(url)

    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"

    for link in relevant_links["links"]:
        link_url = (link.get("url") or "").strip()

        if not link_url:
            print(f"Skipping empty URL: {link.get('type', 'unknown link')}")
            continue

        try:
            result += f"\n\n### Link: {link.get('type', 'unknown link')}\n"
            result += fetch_website_contents(link_url)

        except Exception as error:
            print(f"Skipping unavailable URL: {link_url}")
            print(f"Reason: {error}")

    return result


def build_brochure_prompt(company_name: str, url: str) -> str:
    """
    Assemble the website content for a company and build the full brochure
    user prompt, truncated to MAX_BROCHURE_PROMPT_CHARACTERS.

    :param company_name: Name of the company the brochure is about.
    :param url: Full URL of the company's landing page.
    :return: Complete user prompt ready to send to the LLM.
    """
    website_content = fetch_page_and_all_relevant_links(url)

    user_prompt = get_brochure_user_prompt(
        company_name,
        website_content,
    )

    return truncate_text(
        user_prompt,
        MAX_BROCHURE_PROMPT_CHARACTERS,
    )


def create_brochure(company_name: str, url: str) -> str:
    """
    Generate a company brochure in one LLM call.

    This version prints the generated Markdown directly in the terminal.

    :param company_name: Name of the company the brochure is about.
    :param url: Full URL of the company's landing page.
    :return: Generated brochure text in Markdown.
    """

    # ==========================================
    # OpenAI / GPT Version - Original Code
    # Kept for reference from the notebook.
    # ==========================================

    # response = openai_client.chat.completions.create(
    #     model="gpt-4.1-mini",
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": BROCHURE_SYSTEM_PROMPT,
    #         },
    #         {
    #             "role": "user",
    #             "content": build_brochure_prompt(company_name, url),
    #         },
    #     ],
    # )

    # ==========================================
    # Ollama + Llama 3.2 Version
    # Active implementation.
    # ==========================================

    response = ollama_client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": BROCHURE_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": build_brochure_prompt(company_name, url),
            },
        ],
    )

    result = response.choices[0].message.content

    print("\n--- Company Brochure ---\n")
    print(result)

    return result


def stream_brochure(company_name: str, url: str) -> str:
    """
    Generate a company brochure with streaming output directly in the
    terminal.

    The response is printed chunk-by-chunk to create a typewriter-style
    effect.

    :param company_name: Name of the company the brochure is about.
    :param url: Full URL of the company's landing page.
    :return: Complete generated brochure text in Markdown.
    """

    # ==========================================
    # OpenAI / GPT Version - Original Code
    # Kept for reference from the notebook.
    # ==========================================

    # stream = openai_client.chat.completions.create(
    #     model="gpt-4.1-mini",
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": BROCHURE_SYSTEM_PROMPT,
    #         },
    #         {
    #             "role": "user",
    #             "content": build_brochure_prompt(company_name, url),
    #         },
    #     ],
    #     stream=True,
    # )

    # ==========================================
    # Ollama + Llama 3.2 Version
    # Active implementation.
    # ==========================================

    stream = ollama_client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": BROCHURE_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": build_brochure_prompt(company_name, url),
            },
        ],
        stream=True,
    )

    response = ""

    print("\n--- Company Brochure ---\n")

    for chunk in stream:
        content = chunk.choices[0].delta.content or ""

        response += content

        print(
            content,
            end="",
            flush=True,
        )

    print("\n")

    return response