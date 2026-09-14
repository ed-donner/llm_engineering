import os
from dotenv import load_dotenv
from scraper import fetch_website_links, fetch_website_contents
from openai import OpenAI
import gradio as gr
import json

load_dotenv(override=True)

openai_api_key = os.getenv("OPENAI_API_KEY")

openai_model="gpt-4o-mini"
openai= OpenAI()


system_prompt ="""You are provided with a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:

{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}"""



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



def get_relevant_links(url):
    
    messages = [{"role":"system","content":system_prompt},
                {"role":"user","content":get_links_user_prompt(url)}]

    response = openai.chat.completions.create(model=openai_model,messages=messages,response_format={"type": "json_object"})
    
    result = response.choices[0].message.content
    links = json.loads(result)

    return links


def fetch_page_and_all_relevant_links(url):
    contents = fetch_website_contents(url)
    relevant_links = get_relevant_links(url)
    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
    for link in relevant_links['links']:
        result += f"\n\n### Link: {link['type']}\n"
        result += fetch_website_contents(link["url"])
    return result



def create_brochure(url, company_name):

    system_prompt_2 ="""You are an assistant that analyzes the contents of several relevant pages from a company website
                    and creates a short brochure about the company for prospective customers, investors and recruits.
                    Respond in markdown without code blocks.
                    Include details of company culture, customers and careers/jobs if you have the information.
                    """

    usr_prompt =f"""You are looking at a company called: {company_name}
                    Here are the contents of its landing page and other relevant pages;
                    use this information to build a short brochure of the company in markdown without code blocks.\n\n""" + fetch_page_and_all_relevant_links(url)

    

    response = openai.chat.completions.create(model=openai_model,messages=[{"role":"system","content":system_prompt_2},
                {"role":"user","content":usr_prompt}])



    return response.choices[0].message.content




url = gr.Textbox(label="url")
company_name =gr.Textbox(label="company")

message_output = gr.Markdown(label="Response:")

view = gr.Interface(fn=create_brochure, inputs=[url,company_name], outputs=message_output, flagging_mode="never",title="brochure generator").launch(inbrowser=True, share=False)