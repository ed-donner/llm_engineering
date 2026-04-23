from .llm_handler import call_llm
import logging

logger = logging.getLogger(__name__)

def generate_brochure(company_name, links, model="gpt-4", provider="openai"):
    """Creates a structured markdown brochure using the specified LLM model."""
    system_prompt = """You are an AI that generates a structured company brochure in markdown format. Include an overview, culture, customers, and career opportunities."""

    user_prompt = f"""
    Company: {company_name}
    Website Links: {links}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    return call_llm(messages, model=model, provider=provider)