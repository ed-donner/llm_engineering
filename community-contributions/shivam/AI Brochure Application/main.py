from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
import os
import json
from dotenv import load_dotenv

from scraper import fetch_website_contents, fetch_website_links

load_dotenv(override=True)
api_key = os.getenv("GEMINI_API_KEY")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

client = OpenAI(base_url=GEMINI_BASE_URL, api_key=api_key)
MODEL = 'gemini-flash-lite-latest'

app = FastAPI()

class BrochureRequest(BaseModel):
    company_name: str
    url: str

class BrochureResponse(BaseModel):
    brochure_markdown: str

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

brochure_system_prompt = """
You are an assistant that analyzes the contents of several relevant pages from a company website
and creates a short brochure about the company for prospective customers, investors and recruits.
Respond in markdown without code blocks.
Include details of company culture, customers and careers/jobs if you have the information.
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

def select_relevant_links(url):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(url)}
        ],
        response_format={"type": "json_object"}
    )

    result = response.choices[0].message.content
    return json.loads(result)

def fetch_page_and_all_relevant_links(url):
    contents = fetch_website_contents(url)
    relevant_links = select_relevant_links(url)
    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
    for link in relevant_links['links']:
        result += f"\n\n### Link: {link['type']}\n"
        result += fetch_website_contents(link["url"])
    return result

@app.post("/api/generate")
async def create_brochure_endpoint(request: BrochureRequest):
    try:
        user_prompt_content = fetch_page_and_all_relevant_links(request.url)
        user_prompt_content = user_prompt_content[:5_000] 
        
        user_prompt = f"""
        You are looking at a company called: {request.company_name}
        Here are the contents of its landing page and other relevant pages;
        use this information to build a short brochure of the company in markdown without code blocks.\n\n
        {user_prompt_content}
        """

        def stream_generator():
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": brochure_system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        return StreamingResponse(stream_generator(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/", StaticFiles(directory="static", html=True), name="static")