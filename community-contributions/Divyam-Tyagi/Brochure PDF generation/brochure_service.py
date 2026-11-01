import os
from dotenv import load_dotenv
from fastapi import FastAPI
from scraper import fetch_website_links, fetch_website_contents
from openai import OpenAI
import json
from prompts import *
from schema import *
from IPython.display import Markdown, display
from fastapi import Response
import markdown
from weasyprint import HTML

load_dotenv()

app = FastAPI()

'''
1 - build client first
2 - build the system prompt
3 - call the function to get all links in the string format
4 - make the function to get all the relevant links(use AI)
5 - make the api to generate brochure
'''

client = OpenAI(
    api_key=os.getenv("GROQ_URL"),
    base_url="https://api.groq.com/openai/v1"
)

brochure_messages = [{"role":"system", "content":BROCHURE_SYSTEM_MESSAGE}]
link_messages = [{"role":"system", "content":LINK_SYSTEM_MESSAGE}]

def get_relevant_links(url:str):
    links = fetch_website_links(url)
    user_link_prompt = f'''Here is the list of links on the website {links} -
                    Please decide which of these are relevant web links for a brochure about the company, 
                    respond with the full https URL in JSON format.
                    Do not include Terms of Service, Privacy, email links.
                    Links (some might be relative links):'''
    link_messages.append({"role":"user", "content":user_link_prompt})

    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=link_messages,
        response_format={"type":"json_object"}
    )

    res = resp.choices[0].message.content
    res = json.loads(res)

    return res


@app.post("/api/brochure-generate")
async def generate_brochure(request:InputMode):
    #get the content
    website_content = fetch_website_contents(request.url)
    #get the relevant links
    website_relevant_links = get_relevant_links(request.url)
    user_prompt = f"""
                    You are looking at a company called: {request.company_name}
                    Here are the contents of its landing page and other relevant pages;
                    use this information to build a short brochure of the company in markdown without code blocks.\n\n
                """
    
    user_prompt += '\nwebsite contents = ' + website_content + '\n relevant links' + json.dumps(website_relevant_links)

    brochure_messages.append({"role":"user", "content":user_prompt})

    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=brochure_messages
    )

    markdown_text = resp.choices[0].message.content

    # --- NEW PDF GENERATION LOGIC ---

    # 1. Convert Markdown to HTML
    raw_html = markdown.markdown(markdown_text, extensions=['extra'])

    # 2. Add some CSS styling to make the PDF look like a real brochure
    styled_html = f"""
    <html>
        <head>
            <style>
                @page {{ size: A4; margin: 20mm; }}
                body {{ 
                    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
                    line-height: 1.6; 
                    color: #333;
                }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
                h2 {{ color: #2980b9; margin-top: 30px; }}
                a {{ color: #3498db; text-decoration: none; }}
                ul {{ margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            {raw_html}
        </body>
    </html>
    """

    # 3. Render the HTML to PDF bytes using WeasyPrint
    pdf_bytes = HTML(string=styled_html).write_pdf()

    # 4. Return the PDF file as a direct download!
    safe_company_name = request.company_name.replace(" ", "_").lower()
    filename = f"{safe_company_name}_brochure.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )