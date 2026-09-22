from .llm_handler import call_llm
import logging

logger = logging.getLogger(__name__)

def get_relevant_links(website_name, links, model="gpt-4", provider="openai"):
    """Uses the specified LLM model to decide which links are relevant for a brochure."""

    system_prompt = "You are an AI assistant that selects the most relevant links for a company brochure."
    user_prompt = f"""
    Here are links found on {website_name}'s website. Identify the relevant ones:
    {links}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    return call_llm(messages, model=model, provider=provider)