from summarizer.fetcher import fetch_web_content, format_links
from summarizer.summarizer import get_relevant_links
from summarizer.brochure import generate_brochure
import logging

logger = logging.getLogger(__name__)

def main():
    company_name = input("Enter company name: ") or "HuggingFace"
    url = input("Enter company website: ") or "https://huggingface.co"
    
    model_choice = input("Enter LLM model (default:deepseek-r1:1.5B, gpt-4): ") or "deepseek-r1:1.5B"
    provider_choice = input("Enter provider (openai/ollama(ollama_lib/ollama_api), default: ollama_lib): ") or "ollama_api"

    logger.info(f"Fetching links from {url}...")
    links = fetch_web_content(url)

    if not links:
        logger.error("No links found. Exiting...")
        return

    formatted_links = format_links(url, links)
    logger.info(f"Extracted and formatted {len(formatted_links)} links.")

    relevant_links = get_relevant_links(company_name, formatted_links, model=model_choice, provider=provider_choice)
    logger.info("Filtered relevant links.")

    brochure = generate_brochure(company_name, relevant_links, model=model_choice, provider=provider_choice)
    print("\nGenerated Brochure:\n")
    print(brochure)

if __name__ == "__main__":
    main()