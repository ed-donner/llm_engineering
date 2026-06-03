import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
from scraper import fetch_website_links, fetch_website_contents
# from IPython.display import Markdown, display, update_display

load_dotenv(override=True)
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

gpt_model = "gpt-5-nano"

openai = OpenAI()

if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")

if anthropic_api_key:
    print(f"Anthropic API Key exists and begins {anthropic_api_key[:7]}")
else:
    print("Anthropic API Key not set")

if google_api_key:
    print(f"Google API Key exists and begins {google_api_key[:8]}")
else:
    print("Google API Key not set")

link_system_prompt = """
You are provided with a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:

{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""


def get_links_user_prompt(url):
    user_prompt = f"""
        Here is the list of links on the website {url} -
        Please decide which of these are relevant web links for a brochure about the company,
        respond with the full https URL in JSON format.
        Do not include Terms of Service, Privacy, email links.

        Links (some might be relative links):
    """

    links = fetch_website_links(url)
    user_prompt += "\n".join(links)
    return user_prompt


def select_relevant_links(url, model):
    print(f"Selecting relevant links for {url} by calling {model}")
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(url)},
        ],
        response_format={"type": "json_object"},
    )

    result = response.choices[0].message.content
    links = json.loads(result)
    print(f"Found {len(links['links'])} relevant links")
    return links


# print(select_relevant_links("https://www.homephysiocentre.com/"))


def fetch_page_and_all_relevant_links(url, model):
    contents = fetch_website_contents(url)
    relevant_links = select_relevant_links(url, model)
    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
    for link in relevant_links["links"]:
        result += f"\n\n### Link: {link['type']}\n"
        result += fetch_website_contents(link["url"])
    return result


# print(fetch_page_and_all_relevant_links("https://huggingface.co"))

brochure_system_prompt = """
You are an assistant that analyzes the contents of several relevant pages from a company website
and creates a short brochure about the company for prospective customers, investors and recruits.
Respond in markdown without code blocks.
Include details of company culture, customers and careers/jobs if you have the information.
"""


def get_brochure_user_prompt(company_name, url, model):
    user_prompt = f"""
        You are looking at a company called: {company_name}
        Here are the contents of its landing page and other relevant pages;
        use this information to build a short brochure of the company in markdown without code blocks.\n\n
    """
    user_prompt += fetch_page_and_all_relevant_links(url, model)
    user_prompt = user_prompt[:5_000]  # Truncate if more than 5,000 characters
    return user_prompt

def stream_brochure(company_name, url, model):
    yield "⏳ Going over the website and finding links..."
    links = fetch_website_links(url)

    yield "⏳ Extracting the most relevant links for the brochure..."
    links_prompt = f"""
        Here is the list of links on the website {url} -
        Please decide which of these are relevant web links for a brochure about the company,
        respond with the full https URL in JSON format.
        Do not include Terms of Service, Privacy, email links.

        Links (some might be relative links):
    """
    links_prompt += "\n".join(links)

    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": links_prompt},
        ],
        response_format={"type": "json_object"},
    )
    relevant_links = json.loads(response.choices[0].message.content)

    yield "⏳ Reading the landing page and relevant pages..."
    contents = fetch_website_contents(url)
    website_content = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"

    for link in relevant_links["links"]:
        yield f"⏳ Reading {link['type']}..."
        website_content += f"\n\n### Link: {link['type']}\n"
        website_content += fetch_website_contents(link["url"])

    yield "⏳ Preparing the brochure response..."
    user_prompt = f"""
        You are looking at a company called: {company_name}
        Here are the contents of its landing page and other relevant pages;
        use this information to build a short brochure of the company in markdown without code blocks.\n\n
    """
    user_prompt += website_content
    user_prompt = user_prompt[:5_000]

    stream = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": brochure_system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        stream=True
    )

    brochure = ""
    for chunk in stream:
        brochure += chunk.choices[0].delta.content or ""
        yield brochure
        
name_input = gr.Textbox(label="Company name:")
url_input = gr.Textbox(label="Landing page URL including http:// or https://")
model_selector = gr.Dropdown(["gpt-5-nano","gpt-5.4-nano", "gpt-4.1-nano", "gpt-4o-mini", "gpt-4.1-mini"], label="Select OpenAI model", value="gpt-5-nano")
message_output=gr.Markdown(label="Response:")

view=gr.Interface(
    fn=stream_brochure,
    title="Brochure Generator",
    inputs=[name_input, url_input, model_selector],
    outputs=[message_output],
    examples=[
            ["Hugging Face", "https://huggingface.co", "gpt-5-nano"],
            ["Edward Donner", "https://edwarddonner.com", "gpt-4o-mini"]
        ], 
    flagging_mode="never"
)

view.launch()
