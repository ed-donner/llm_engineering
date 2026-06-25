import json
import os
from dotenv import load_dotenv
from IPython.display import Markdown, display, update_display
from openai import OpenAI
from scrapper import fetch_website_content, fetch_website_links

load_dotenv()
apikey = os.getenv("OPENROUTER_API_KEY")

# Ensure Ollama is running locally before executing
ollama_url = "http://localhost:11434/v1"
ollama = OpenAI(base_url=ollama_url, api_key='ollama')

def create_brochure(name, url):
    # Fetching landing page content
    content = fetch_website_content(url)

    # Fetching links
    def makeprompt(links):
        system_prompt = """
        You are provided with a list of links found on a webpage.
        You are able to decide which of the links would be most relevant to include in a brochure 
        about the company. You must respond strictly in JSON as in this example:
        {
            "links": [
                {"type": "about page", "url": "https://example.com/about"},
                {"type": "careers page", "url": "https://example.com/careers"}
            ]
        }
        """
        user_prompt = f"""
        Here is the list of links on the website {links} -
        Please decide which of these are relevant web links for a brochure about the company, 
        respond with the full https URL in JSON format.
        Do not include Terms of Service, Privacy, email links.
        """
        return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

    # FIX: Use the dynamic url argument instead of the hardcoded string
    urls = fetch_website_links(url)
    prompt = makeprompt(urls)
    
    response = ollama.chat.completions.create(
        model="llama3.2",
        messages=prompt,
        response_format={"type": "json_object"}
    )
    
    print("By Ollama LOCAL MODEL: ")
    result = response.choices[0].message.content
    links = json.loads(result)
    
    # Combine content
    final_res = f"## Landing Page:\n\n{content}\n## Relevant Links:\n"
    
    # Safely iterate through the links returned by the LLM
    if 'links' in links and isinstance(links['links'], list):
        for link in links['links']:
            final_res += f"\n\n### Link: {link.get('type', 'More Info')}\n"
            final_res += fetch_website_content(link.get("url"))
  
    brochure_system_prompt = """
    You are an assistant that analyzes the contents of several relevant pages from a company website
    and creates a short brochure about the company for prospective customers, investors and recruits.
    Respond in markdown without code blocks.
    Include details of company culture, customers and careers/jobs if you have the information.
    """
    
    user_prompt = f"You are looking at a company called: {name}\n"
    user_prompt += "Here are the contents of its landing page and other relevant pages:\n\n"
    user_prompt += final_res[:3_000] # Limiting context window length

    # Streamed output setup
    stream = ollama.chat.completions.create(
        model="llama3.2",
        messages=[
            {"role": "system", "content": brochure_system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        stream=True
    )


    
    print("\n--- Generating Brochure ---\n")
    full_response = ""
    
    for chunk in stream:
        content = chunk.choices[0].delta.content or ""
        full_response += content
        # Print each chunk instantly to the terminal without adding a newline
        print(content, end="", flush=True)
        
    print("\n\n--- Generation Complete ---")

# Execute function
create_brochure("Edward", "https://edwarddonner.com/")
