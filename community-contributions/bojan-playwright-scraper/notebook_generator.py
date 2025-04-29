import sys
import os
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell
import asyncio
from dotenv import load_dotenv
import logging

# Učitavanje .env varijabli
load_dotenv()

# Postavljanje logginga
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Dodavanje direktorija projekta u sys.path
project_dir = os.path.join(
    "/home/lakov/projects/llm_engineering",
    "community-contributions/playwright-bojan"
)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Uvoz analyze_content iz playwright_ai_scraper.py
try:
    from playwright_ai_scraper import analyze_content
except ModuleNotFoundError as e:
    logging.error(f"Error importing module: {e}")
    sys.exit(1)

# Funkcija za spremanje notebooka


def save_notebook(url, content):
    output_dir = os.path.join(project_dir, "notebooks")
    os.makedirs(output_dir, exist_ok=True)

    # Izvlačenje domene iz URL-a
    domain = url.split("//")[-1].split("/")[0].replace(".", "_")
    filename = f"{domain}_Summary.ipynb"
    path = os.path.join(output_dir, filename)

    nb = new_notebook()
    intro = f"""
# Summary for {url}

This notebook contains an AI-generated summary of the website content.

**URL**: `{url}`

---
**Analysis**:
{content}
"""
    nb.cells.append(new_markdown_cell(intro))

    with open(path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)

    logging.info(f"Notebook saved to: {path}")
    return path

# Glavna funkcija


async def main():
    url = input("Enter URL to scrape: ")
    try:
        result = await analyze_content(url, headless=True)
        save_notebook(url, result)
        print(f"Summary for {url}:\n{result}")
    except Exception as e:
        logging.error(f"Failed to process {url}: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
