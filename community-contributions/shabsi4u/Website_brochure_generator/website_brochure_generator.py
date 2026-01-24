from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
import json
from typing import List
from bs4 import BeautifulSoup

# Rich library for beautiful terminal markdown rendering
from rich.console import Console
from rich.markdown import Markdown as RichMarkdown

def get_client_and_headers():
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key.startswith('sk-proj-') and len(api_key)>10:
        # print("API key looks good so far")
        pass
    else:
        print("There might be a problem with your API key")

    client = OpenAI(api_key=api_key)
    
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    }
    return client, headers

# Utility methods to display content in markdown format
def print_markdown_terminal(text):
    """Print markdown-formatted text to terminal with beautiful formatting using Rich"""
    console = Console()
    console.print(RichMarkdown(text))

def display_content(content, is_markdown=True):
    """Display content using Rich formatting"""
    if is_markdown:
        print_markdown_terminal(content)
    else:
        print(content)

def stream_content(response, title="Content"):
    """
    Utility function to handle streaming content display using Rich
    
    Args:
        response: OpenAI streaming response object
        title (str): Title to display for the streaming content
    
    Returns:
        str: Complete streamed content
    """
    result = ""
    console = Console()
    
    # Terminal streaming with real-time output using Rich
    console.print(f"\n[bold blue]{title}...[/bold blue]\n")
    for chunk in response:
        content = chunk.choices[0].delta.content or ""
        result += content
        # Print each chunk as it arrives for streaming effect
        print(content, end='', flush=True)
    console.print(f"\n\n[bold green]{'='*50}[/bold green]")
    console.print(f"[bold green]{title.upper()} COMPLETE[/bold green]")
    console.print(f"[bold green]{'='*50}[/bold green]")
    
    return result

# Utility class to get the contents of a website
class Website:
    def __init__(self, url):
        self.url = url
        self.client, self.headers = get_client_and_headers()
        response = requests.get(url, headers=self.headers)
        self.body = response.content
        soup = BeautifulSoup(self.body, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.text = ""
        links = [link.get('href') for link in soup.find_all('a')]
        self.links = [link for link in links if link]        

    def get_contents(self):
        return f"Webpage Title: {self.title}\nWebpage Contents: {self.text}\n\n"

def get_links_system_prompt():
    link_system_prompt = """"You are provided with a list of links found on a webpage. \
        You are able to decide which of the links would be most relevant to include in a brochure about the company. \
        Relevant links usually include: About page, or a Company page, or Careers/Jobs pages or News page\n"""
    link_system_prompt += "Always respond in JSON exactly like this: \n"
    link_system_prompt += """
        {
            "links": [
                {"type": "<page type>", "url": "<full URL>"},
                {"type": "<page type>", "url": "<full URL>"}
            ]
        }\n
    """
    link_system_prompt += """ If no relevant links are found, return:
        {
            "links": []
        }\n
    """
    link_system_prompt += "If multiple links could map to the same type (e.g. two About pages), include the best candidate only.\n"

    link_system_prompt += "You should respond in JSON as in the below examples:\n"
    link_system_prompt += """
        ## Example 1
        Input links:
        - https://acme.com/about  
        - https://acme.com/pricing  
        - https://acme.com/blog  
        - https://acme.com/signup  

        Output:
        {
        "links": [
            {"type": "about page", "url": "https://acme.com/about"},
            {"type": "blog page", "url": "https://acme.com/blog"},
            {"type": "pricing page", "url": "https://acme.com/pricing"}
        ]
        }
        """
    link_system_prompt += """
        ## Example 2
        Input links:
        - https://startup.io/  
        - https://startup.io/company  
        - https://startup.io/careers  
        - https://startup.io/support  

        Output:
        {
        "links": [
            {"type": "company page", "url": "https://startup.io/company"},
            {"type": "careers page", "url": "https://startup.io/careers"}
        ]
        }
        """
    link_system_prompt += """
        ## Example 3
        Input links:
        - https://coolapp.xyz/login  
        - https://coolapp.xyz/random  

        Output:
        {
        "links": []
        }
        """
    return link_system_prompt

def get_links_user_prompt(website):
    user_prompt = f"Here is the list of links on the website of {website.url} - "
    user_prompt += "please decide which of these are relevant web links for a brochure about the company, respond with the full https URL in JSON format. \n"
    user_prompt += "Do not include Terms of Service, Privacy, email links.\n"
    user_prompt += "Links (some might be relative links):\n"
    user_prompt += "\n".join(website.links)
    return user_prompt

def get_brochure_system_prompt():
    brochure_system_prompt = """
        You are an assistant that analyzes the contents of several relevant pages from a company website \
        and creates a short brochure about the company for prospective customers, investors and recruits. Respond in markdown.
        Include details of company culture, customers and careers/jobs if you have the information.
    """
    return brochure_system_prompt

def get_brochure_user_prompt(url):
    user_prompt = f"You are looking at a company details of: {url}\n"
    user_prompt += f"Here are the contents of its landing page and other relevant pages; use this information to build a short brochure of the company in markdown.\n"
    user_prompt += get_details_for_brochure(url)
    user_prompt = user_prompt[:15000] # Truncate if more than 15,000 characters
    return user_prompt

def get_translation_system_prompt(target_language):
    translation_system_prompt = f"You are a professional translator specializing in business and marketing content. \
    Translate the provided brochure to {target_language} while maintaining all formatting and professional tone."
    return translation_system_prompt

def get_translation_user_prompt(original_brochure, target_language):
    translation_prompt = f"""
    You are a professional translator. Please translate the following brochure content to {target_language}.
    
    Important guidelines:
    - Maintain the markdown formatting exactly as it appears
    - Keep all headers, bullet points, and structure intact
    - Translate the content naturally and professionally
    - Preserve any company names, product names, or proper nouns unless they have established translations
    - Maintain the professional tone and marketing style
    
    Brochure content to translate:
    {original_brochure}
    """
    return translation_prompt

def get_links(url):
    website = Website(url)
    response = website.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": get_links_system_prompt()},
            {"role": "user", "content": get_links_user_prompt(website)}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    print("get_links:", result)
    return json.loads(result)

def get_details_for_brochure(url):
    website = Website(url)
    result = "Landing page:\n"
    result += website.get_contents()
    links = get_links(url)
    print("Found links:", links)
    for link in links["links"]:
        result += f"\n\n{link['type']}\n"
        result += Website(link["url"]).get_contents()
    return result

def create_brochure(url):
    website = Website(url)
    response = website.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": get_brochure_system_prompt()},
            {"role": "user", "content": get_brochure_user_prompt(url)}
        ]
    )
    result = response.choices[0].message.content
    display_content(result, is_markdown=True)
    return result

def stream_brochure(url):
    website = Website(url)
    response = website.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": get_brochure_system_prompt()},
            {"role": "user", "content": get_brochure_user_prompt(url)}
        ],
        stream=True
    )
    
    # Use the reusable streaming utility function
    result = stream_content(response, "Generating brochure")
    return result

def translate_brochure(url, target_language="Spanish", stream_mode=False):
    """
    Generate a brochure and translate it to the target language
    
    Args:
        url (str): The website URL to generate brochure from
        target_language (str): The target language for translation (default: "Spanish")
        stream_mode (bool): Whether to use streaming output (default: False)
    
    Returns:
        str: Translated brochure content
    """
    # First generate the original brochure
    original_brochure = create_brochure(url)
    
    # Get translation prompts
    translation_system_prompt = get_translation_system_prompt(target_language)
    translation_user_prompt = get_translation_user_prompt(original_brochure, target_language)
    
    # Get OpenAI client
    website = Website(url)
    
    if stream_mode:
        # Generate translation using OpenAI with streaming
        response = website.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": translation_system_prompt},
                {"role": "user", "content": translation_user_prompt}
            ],
            stream=True
        )
        
        # Use the reusable streaming utility function
        translated_brochure = stream_content(response, f"Translating brochure to {target_language}")
    else:
        # Generate translation using OpenAI with complete output
        response = website.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": translation_system_prompt},
                {"role": "user", "content": translation_user_prompt}
            ]
        )
        
        translated_brochure = response.choices[0].message.content
        
        # Display the translated content
        display_content(translated_brochure, is_markdown=True)
    
    return translated_brochure


# Main function for terminal usage
def main():
    """Main function for running the brochure generator from terminal"""
    import sys
    
    if len(sys.argv) != 2:
        console = Console()
        console.print("[bold red]Usage:[/bold red] python website_brochure_generator.py <website_url>")
        console.print("[bold blue]Example:[/bold blue] python website_brochure_generator.py https://example.com")
        sys.exit(1)
    
    url = sys.argv[1]
    console = Console()
    
    console.print(f"[bold green]Generating brochure for:[/bold green] {url}")
    console.print("\n[bold yellow]Choose display mode:[/bold yellow]")
    console.print("1. Complete output (display all at once)")
    console.print("2. Stream output (real-time generation)")
    
    display_choice = input("\nEnter choice (1 or 2): ").strip()
    
    # Generate brochure based on display choice
    if display_choice == "1":
        result = create_brochure(url)
    elif display_choice == "2":
        result = stream_brochure(url)
    else:
        console.print("[bold red]Invalid choice. Using default: complete output[/bold red]")
        result = create_brochure(url)
    
    # Ask if user wants translation
    console.print("\n[bold yellow]Translation options:[/bold yellow]")
    console.print("1. No translation (original only)")
    console.print("2. Translate to another language")
    
    translation_choice = input("\nEnter choice (1 or 2): ").strip()
    
    if translation_choice == "2":
        target_language = input("Enter target language (e.g., Spanish, French, German, Chinese): ").strip()
        if not target_language:
            target_language = "Spanish"
        
        # Pass the stream mode based on the display choice
        stream_mode = (display_choice == "2")
        translate_brochure(url, target_language, stream_mode=stream_mode)      
    else:
        pass

if __name__ == "__main__":
    main()