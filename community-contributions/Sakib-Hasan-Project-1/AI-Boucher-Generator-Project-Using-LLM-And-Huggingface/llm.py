import json
from groq import Groq


# ============================================================
# 1. PREPARE INPUT FOR BROCHURE GENERATION
# ============================================================

def prepare_llm_input(scraped_data):
    """
    Convert scraped website data into a prompt
    for the LLM.
    """

    return f"""
Analyze the following scraped website data and
create professional brochure content.

WEBSITE:
{scraped_data.get("website", "")}

TITLE:
{scraped_data.get("title", "")}

HEADINGS:
{scraped_data.get("headings", [])}

PARAGRAPHS:
{scraped_data.get("paragraphs", [])}

IMPORTANT LINKS:
{scraped_data.get("important_links", [])}


Return ONLY valid JSON using exactly this structure:

{{
    "company_overview": "...",

    "products_services": [
        "...",
        "..."
    ],

    "key_features": [
        "...",
        "..."
    ],

    "mission": "...",

    "important_information": "..."
}}

IMPORTANT RULES:

- Return ONLY JSON.
- Do not use Markdown.
- Do not use ```json.
- Do not write explanations.
- Do not add extra keys.
- Do not invent information.
- Use only information supported by the website.
"""


# ============================================================
# 2. GENERATE BROCHURE CONTENT
# ============================================================

def generate_brochure_content(client, scraped_data):
    """
    Send scraped website data to Groq
    and return structured brochure content.
    """

    llm_input = prepare_llm_input(
        scraped_data
    )

    response = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[
            {
                "role": "system",
                "content": """
You are a professional AI brochure generator.

Always return valid JSON.
Never return Markdown or explanations.
"""
            },
            {
                "role": "user",
                "content": llm_input
            }
        ],

        temperature=0.3,

        response_format={
            "type": "json_object"
        }
    )

    raw_output = response.choices[0].message.content

    brochure_data = json.loads(
        raw_output
    )

    return brochure_data


# ============================================================
# 3. GENERATE IMAGE PROMPT
# ============================================================

def generate_image_prompt(client, brochure_data):
    """
    Use the generated brochure content to create
    a professional prompt for the image generation model.
    """

    image_prompt_input = f"""
Create ONE professional image-generation prompt
for a corporate business brochure.

Use ONLY the information provided below.

COMPANY OVERVIEW:
{brochure_data.get("company_overview", "")}

PRODUCTS AND SERVICES:
{brochure_data.get("products_services", [])}

KEY FEATURES:
{brochure_data.get("key_features", [])}

MISSION:
{brochure_data.get("mission", "")}


IMAGE REQUIREMENTS:

- Professional corporate photography
- Modern business environment
- Realistic and visually appealing
- Suitable for a professional company brochure
- The image should visually represent the company,
  its services, technology, or main activities
- Clean and premium composition
- Good lighting
- High visual quality
- No text
- No letters
- No logos
- No watermark
- Do not create a poster
- Do not create a brochure layout

Return ONLY the image generation prompt.
Do not add explanations.
Do not use Markdown.
"""


    response = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[
            {
                "role": "system",
                "content": """
You are an expert AI image prompt engineer.

Your job is to convert company information
into a concise, realistic, professional
image-generation prompt.

Return ONLY the prompt.
"""
            },
            {
                "role": "user",
                "content": image_prompt_input
            }
        ],

        temperature=0.5
    )


    image_prompt = response.choices[0].message.content.strip()

    return image_prompt