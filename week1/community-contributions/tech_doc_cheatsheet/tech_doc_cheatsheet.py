# imports
import os
import json
from dotenv import load_dotenv
from scraper_modified import fetch_website_links, fetch_website_contents
from openai import OpenAI

load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

if not(api_key and api_key.startswith('sk-proj-') and len(api_key)>10):
    print("There might be a problem with your API key.")
    
MODEL4o = 'gpt-4o-mini'
MODEL5nano = 'gpt-5-nano'
openai = OpenAI()

#Selecting the links
############################################################

# Prompts for seleting the links

link_system_prompt = """
You are provided with a list of links found on tech documentation page.
You are able to decide which of the links would be most relevant AND specific for beginners to learn about this technology.
You should respond in JSON as in this example:

{
    "links": [
        {"type": "installation", "url": "https://tailwindcss.com/docs/installation/"},
        {"type": "Styling with utility classes", "url": "https://tailwindcss.com/docs/styling-with-utility-classes"}
    ]
}
"""

def get_links_user_prompt(url):
    user_prompt = f"""
Here is the list of links on the website {url} -
Please decide which of these are relevant web links for beginners to learn about this technology 
respond with the full https URL in JSON format.

Links (some might be relative links):

"""
    links = fetch_website_links(url)
    user_prompt += "\n".join(links)
    return user_prompt


# selecting link using gpt-4-mini
def select_relevant_links(url):
    response = openai.chat.completions.create(
        model=MODEL5nano,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(url)}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    links = json.loads(result)
    return links

select_relevant_links("https://tailwindcss.com/docs/installation/using-vite")


#Making cheatsheet
############################################################
cheatsheet_system_prompt = """
You will be provided contents from technology documentations, 
and you will make a cheatsheet to help users memorize and study it.
Respond in markdown without code blocks.
"""

def fetch_page_and_all_relevant_links(url):
    contents = fetch_website_contents(url)
    relevant_links = select_relevant_links(url)
    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
    for link in relevant_links['links']:
        result += f"\n\n### {link['type']}\n"
        result += fetch_website_contents(link["url"])
    return result

def cheatsheet_user_prompt(url):
    # f is below to enable expression {} in the string
    user_prompt = f"""
Please provide a clear, simple cheatsheet summarizing the content below to help beginners learn and use this technology.
You should involve simplified sample code.

"""
    user_prompt += fetch_page_and_all_relevant_links(url)
    user_prompt = user_prompt[:7_000] # Truncate if more than 7,000 characters
    return user_prompt

def create_cheatsheet(url):
    response = openai.chat.completions.create(
        model=MODEL4o,
        messages=[
            {"role": "system", "content": cheatsheet_system_prompt},
            {"role": "user", "content": cheatsheet_user_prompt(url)}
        ],
    )
    return response.choices[0].message.content

create_cheatsheet("https://tailwindcss.com/docs/installation/using-vite")


#Main function
############################################################
def main():
    url = input("Enter a documentation URL to making cheatsheet: ")
    print("\nMaking cheatsheet...\n")
    cheatsheet = create_cheatsheet(url)
    print(cheatsheet)


if __name__ == "__main__":
    main()
