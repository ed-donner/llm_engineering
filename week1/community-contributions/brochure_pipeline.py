"""
Brochure Generation Pipeline
----------------------------
Scrapes a company website.

Identifies the most relevant pages (About, Careers, etc.).

Generates a witty, engaging company brochure.

Translates it into a chosen language.

Produces a concise executive summary.

Extracts structured company data (JSON format).

Saves all outputs locally for easy sharing.
"""

import os
import json
from datetime import datetime
from IPython.display import Markdown, display
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------
# Initialization and Constants
# ---------------------------------------------------------------------

load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("❌ Missing OPENAI_API_KEY in environment. Add it to your .env file.")

openai = OpenAI(api_key=api_key)

MODEL = "gpt-5-nano"

# ---------------------------------------------------------------------
# Utility Functions: Simple Web Scraper
# ---------------------------------------------------------------------

def fetch_website_links(url):
    """Fetch all hyperlinks from a given URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"⚠️ Error fetching links from {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href.startswith("#") or href.startswith("mailto:"):
            continue
        if not href.startswith("http"):
            href = os.path.join(url, href)
        links.append(href)
    return list(set(links))

def fetch_website_contents(url):
    """Fetch visible text content from a webpage."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"⚠️ Error fetching content from {url}: {e}")
        return ""
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(separator="\n")
    return text.strip()[:4000]  # limit to 4000 chars for token safety

# ---------------------------------------------------------------------
# Step 1: Select Relevant Links
# ---------------------------------------------------------------------

link_system_prompt = """
You are provided with a list of links found on a webpage.
Decide which links are most relevant to include in a brochure about the company,
such as About, Company, Careers, or Blog pages.
Respond in JSON as:
{
  "links": [
    {"type": "about page", "url": "https://example.com/about"},
    {"type": "careers page", "url": "https://example.com/careers"}
  ]
}
"""

def get_links_user_prompt(url):
    """Compose the user prompt listing discovered links."""
    links = fetch_website_links(url)
    user_prompt = f"""
Here is the list of links found on the website {url}.
Please identify which are relevant for a company brochure (no privacy or terms links):

{chr(10).join(links)}
"""
    return user_prompt

def select_relevant_links(url):
    """Call GPT to select relevant company links."""
    print(f"Selecting relevant links for {url} by calling {MODEL}")
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(url)}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    links = json.loads(result)
    print(f"Found {len(links['links'])} relevant links")
    return links

# ---------------------------------------------------------------------
# Step 2: Build Brochure Base Content
# ---------------------------------------------------------------------

brochure_system_prompt = """
You are an assistant that analyzes several relevant pages from a company website
and creates a short, humorous, entertaining brochure for customers, investors, and recruits.
Respond in markdown (no code blocks).
Include company culture, customers, and career information if available.
"""

def fetch_page_and_all_relevant_links(url):
    """Fetch main page and all relevant linked pages."""
    contents = fetch_website_contents(url)
    relevant_links = select_relevant_links(url)
    result = f"## Landing Page:\n\n{contents}\n\n## Relevant Links:\n"
    for link in relevant_links["links"]:
        result += f"\n\n### {link['type'].capitalize()}\n"
        result += fetch_website_contents(link["url"])
    return result[:10000]  # safety cutoff

def get_brochure_user_prompt(company_name, url):
    """Compose brochure creation prompt."""
    user_prompt = f"""
You are looking at a company called: {company_name}
Here are its landing page and relevant pages. Use this to build a short witty brochure:

"""
    user_prompt += fetch_page_and_all_relevant_links(url)
    return user_prompt[:5000]

# ---------------------------------------------------------------------
# Step 3–6: Complete Multi-Step Brochure Pipeline
# ---------------------------------------------------------------------

def generate_complete_brochure_pipeline(company_name, url, language="English", save_outputs=True):
    """
    Complete 5-step intelligent brochure pipeline:
      1. Select relevant links.
      2. Generate main English brochure.
      3. Enhance/translate to target language.
      4. Produce executive summary.
      5. Extract structured company data (JSON).
      6. (optional) Save all results to local files.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = company_name.lower().replace(" ", "_")
    output_dir = f"./brochure_outputs/{safe_name}_{timestamp}"
    if save_outputs:
        os.makedirs(output_dir, exist_ok=True)

    # Step 1 -----------------------------------------------------
    print(f"=== Step 1: Selecting relevant links for {company_name} ===")
    relevant_links = select_relevant_links(url)
    print(f"Found {len(relevant_links['links'])} relevant links.\n")

    # Step 2 -----------------------------------------------------
    print(f"=== Step 2: Generating main brochure ===")
    brochure_prompt = get_brochure_user_prompt(company_name, url)
    brochure_response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": brochure_system_prompt},
            {"role": "user", "content": brochure_prompt}
        ]
    )
    main_brochure = brochure_response.choices[0].message.content
    print(f"Main brochure created (≈{len(main_brochure)} chars)\n")

    # Step 3 -----------------------------------------------------
    print(f"=== Step 3: Enhancing / Translating brochure to {language} ===")
    enhancement_system_prompt = f"""
You are a skilled marketing writer and translator.
Rewrite the provided brochure to be more engaging, witty, and persuasive
while translating it entirely into {language}. Keep humor, tone, and markdown formatting.
"""
    enhancement_user_prompt = f"""
Company: **{company_name}**
Website: {url}

Below is the original English brochure.
Please rewrite and translate it into **{language}**, keeping the style, humor, and structure.

--- ORIGINAL BROCHURE ---
{main_brochure}
"""
    enhancement_response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": enhancement_system_prompt},
            {"role": "user", "content": enhancement_user_prompt}
        ]
    )
    translated_brochure = enhancement_response.choices[0].message.content
    print(f"Translated brochure ready.\n")

    # Step 4 -----------------------------------------------------
    print(f"=== Step 4: Creating Executive Summary ===")
    summary_system_prompt = """
You are a professional marketing strategist.
Write a concise, polished summary of the following brochure suitable for:
 - Investors or executives
 - LinkedIn bios or company overviews
Keep it under 150 words, in the same language as the brochure.
Respond in plain text (no markdown).
"""
    summary_user_prompt = f"""
Company: {company_name}
Language: {language}
Brochure:
{translated_brochure}
"""
    summary_response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": summary_system_prompt},
            {"role": "user", "content": summary_user_prompt}
        ]
    )
    executive_summary = summary_response.choices[0].message.content
    print("✅ Executive summary generated.\n")

    # Step 5 -----------------------------------------------------
    print(f"=== Step 5: Extracting structured company data ===")
    data_extraction_system_prompt = """
You are a business intelligence assistant.
Analyze the following brochure and extract structured company information in JSON format.
Return only valid JSON (no markdown).
Fields:
{
  "company_name": "",
  "industry": "",
  "headquarters": "",
  "founded_year": "",
  "products_or_services": "",
  "mission_or_vision": "",
  "estimated_employees": "",
  "target_audience": "",
  "key_values_or_culture": ""
}
"""
    data_extraction_user_prompt = f"""
Company: {company_name}
Language: {language}
Brochure text:
{translated_brochure}
"""
    data_response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": data_extraction_system_prompt},
            {"role": "user", "content": data_extraction_user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    structured_data = json.loads(data_response.choices[0].message.content)
    print("📊 Structured company data extracted.\n")

    # Step 6 -----------------------------------------------------
    if save_outputs:
        print(f"💾 Saving outputs to {output_dir}")
        with open(os.path.join(output_dir, "01_relevant_links.json"), "w", encoding="utf-8") as f:
            json.dump(relevant_links, f, indent=2, ensure_ascii=False)
        with open(os.path.join(output_dir, "02_main_brochure_en.md"), "w", encoding="utf-8") as f:
            f.write(main_brochure)
        with open(os.path.join(output_dir, f"03_brochure_{language}.md"), "w", encoding="utf-8") as f:
            f.write(translated_brochure)
        with open(os.path.join(output_dir, "04_executive_summary.txt"), "w", encoding="utf-8") as f:
            f.write(executive_summary)
        with open(os.path.join(output_dir, "05_structured_data.json"), "w", encoding="utf-8") as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        print("✅ All files saved successfully.\n")

    # Final Output Display
    display(Markdown(f"# 🌍 {language} Brochure\n\n{translated_brochure}"))
    display(Markdown(f"---\n### 🧭 Executive Summary\n\n{executive_summary}"))
    display(Markdown(f"---\n### 📊 Structured Company Data\n```json\n{json.dumps(structured_data, indent=2)}\n```"))

    return {
        "relevant_links": relevant_links,
        "main_brochure": main_brochure,
        "translated_brochure": translated_brochure,
        "executive_summary": executive_summary,
        "structured_data": structured_data,
        "output_dir": output_dir
    }

# ---------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------
if __name__ == "__main__":
    result = generate_complete_brochure_pipeline(
        "Karczma w Komorowicach",
        "https://www.karczmawkomorowicach.pl/",
        language="Polish",
        save_outputs=True
    )
