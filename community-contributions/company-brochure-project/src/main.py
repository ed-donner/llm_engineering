"""
main.py
-------

Program entry point. Responsible only for:

* user interaction (collecting company name and website URL)
* calling the brochure-generation pipeline
* printing / streaming the resulting brochure

No scraping logic, prompt definitions, or LLM client setup lives here.
"""

from __future__ import annotations

from brochure import stream_brochure


def get_company_name() -> str:
    """Prompt the user for the company name."""
    return input("Enter the company name: ").strip()


def get_company_url() -> str:
    """Prompt the user for the company's website URL."""
    return input(
        "Enter the company website URL (e.g. https://example.com): "
    ).strip()


def main() -> None:
    """
    Collect the company name and website URL, then generate
    and stream the company brochure.
    """
    company_name = get_company_name()
    url = get_company_url()

    print(
        f"\nGenerating brochure for '{company_name}' "
        f"({url}) using local Llama 3.2 via Ollama...\n"
    )

    stream_brochure(company_name, url)


if __name__ == "__main__":
    main()