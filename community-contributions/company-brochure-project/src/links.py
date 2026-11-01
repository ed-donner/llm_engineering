"""
links.py
--------

Responsible only for:

* selecting the company links relevant to a brochure
* building the link-selection user prompt (delegated to prompts.py)
* calling the LLM to classify/select links
* parsing and returning the resulting JSON

No brochure-generation logic lives here.
"""

from __future__ import annotations

from typing import Any

from llm import MODEL, ollama_client
from prompts import LINK_SYSTEM_PROMPT, get_links_user_prompt
from utils import parse_json_response


def select_relevant_links(url: str) -> dict[str, Any]:
    """
    Ask the LLM to select the links on the given website that are most
    relevant for building a company brochure.

    :param url: Full URL of the company website to inspect.
    :return: A dictionary of the form {"links": [{"type": ..., "url": ...}, ...]}.
    """
    print(f"Selecting relevant links for {url} by calling {MODEL}")

    # ==========================================
    # OpenAI / GPT Version - Original Code (kept for reference)
    # ==========================================
    #
    # response = openai_client.chat.completions.create(
    #     model=MODEL,
    #     messages=[
    #         {"role": "system", "content": LINK_SYSTEM_PROMPT},
    #         {"role": "user", "content": get_links_user_prompt(url)}
    #     ],
    #     response_format={"type": "json_object"}
    # )

    # ==========================================
    # Ollama + Llama 3.2 Version - active implementation
    # ==========================================

    response = ollama_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": LINK_SYSTEM_PROMPT},
            {"role": "user", "content": get_links_user_prompt(url)},
        ],
        response_format={"type": "json_object"},
    )

    result = response.choices[0].message.content

    links = parse_json_response(result)

    print(f"Found {len(links['links'])} relevant links")

    return links
