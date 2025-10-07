import os
import openai
import requests
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import gradio as gr
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Generator
import logging
from prompts import (
    get_links_system_prompt,
    get_links_user_prompt,
    get_brochure_system_prompt,
    get_brochure_user_prompt
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configurations
MODEL_CONFIGS = {
    "openai": {
        "model": "gpt-4o-mini",
        "base_url": None,
        "env_key": "OPENAI_API_KEY",
        "key_prefix": "sk-proj-"
    },
    "anthropic": {
        "model": "claude-3-5-sonnet-20240620",
        "base_url": "https://api.anthropic.com/v1",
        "env_key": "ANTHROPIC_API_KEY",
        "key_prefix": "sk-ant-"
    },
    "gemini": {
        "model": "gemini-2.0-flash-exp",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "env_key": "GOOGLE_API_KEY",
        "key_prefix": None
    }
}

# HTTP headers for web scraping
SCRAPING_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


class LLMInterface:
    """Handles LLM API interactions with stateful client management."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.config = MODEL_CONFIGS.get(model_name)
        if not self.config:
            raise ValueError(f"Unsupported model: {model_name}")
        
        self.client = self._create_client()
        logger.info(f"Initialized LLM interface for {model_name}")
    
    def _create_client(self) -> openai.OpenAI:
        """Create and configure the OpenAI client for the specified model."""
        api_key = self._get_api_key()
        
        client_kwargs = {
            "api_key": api_key
        }
        
        if self.config["base_url"]:
            client_kwargs["base_url"] = self.config["base_url"]
        
        return openai.OpenAI(**client_kwargs)
    
    def _get_api_key(self) -> str:
        """Get and validate the API key for the current model."""
        load_dotenv(override=True)
        key = os.getenv(self.config["env_key"])
        
        if not key:
            raise ValueError(f"{self.config['env_key']} is not set")
        
        if self.config["key_prefix"] and not key.startswith(self.config["key_prefix"]):
            raise ValueError(f"{self.config['env_key']} is not valid")
        
        return key
    
    def query_stream(self, user_prompt: str, system_prompt: str) -> Generator[str, None, None]:
        """Stream a response from the LLM."""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            stream = self.client.chat.completions.create(
                model=self.config["model"],
                messages=messages,
                stream=True
            )
            
            result = ""
            for chunk in stream:
                result = chunk.choices[0].delta.content or ""
                yield result
                    
        except Exception as e:
            logger.error(f"Error in LLM query: {e}")
            yield f"Error: {str(e)}"
    
    def query_json(self, user_prompt: str, system_prompt: str) -> Dict:
        """Get a structured JSON response from the LLM."""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            return json.loads(result)

        except Exception as e:
            logger.error(f"Error in LLM JSON query: {e}")
            return {"error": str(e)}


def validate_url(url: str) -> bool:
    """Validate if the URL is properly formatted."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def scrape_website(url: str) -> Dict:
    """Scrape website content and return structured data."""
    if not validate_url(url):
        raise ValueError(f"Invalid URL: {url}")
    
    try:
        logger.info(f"Scraping website: {url}")
        response = requests.get(url, headers=SCRAPING_HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.title.string.strip() if soup.title and soup.title.string else "No title found"
        
        # Clean and extract text content
        text_content = ""
        if soup.body:
            # Remove irrelevant elements
            for element in soup.body(["script", "style", "img", "input", "button", "nav", "footer"]):
                element.decompose()
            
            text_content = soup.body.get_text(separator="\n", strip=True)
        
        # Extract all links
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                # Convert relative URLs to absolute
                absolute_url = urljoin(url, href)
                link_text = link.get_text(strip=True)
                links.append({
                    "url": absolute_url,
                    "text": link_text,
                    "href": href
                })
        
        return {
            "url": url,
            "title": title,
            "content": text_content,
            "links": links,
            "status": "success"
        }
        
    except requests.RequestException as e:
        logger.error(f"Network error scraping {url}: {e}")
        return {"url": url, "error": f"Network error: {str(e)}", "status": "error"}
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return {"url": url, "error": f"Scraping error: {str(e)}", "status": "error"}




def get_relevant_links(website_data: Dict, llm_interface: LLMInterface) -> List[Dict]:
    """Get relevant links for brochure generation using LLM analysis."""
    try:
        system_prompt = get_links_system_prompt()
        user_prompt = get_links_user_prompt(website_data)
        
        result = llm_interface.query_json(user_prompt, system_prompt)
        
        if "error" in result:
            logger.error(f"Error getting relevant links: {result['error']}")
            return []
        
        return result.get("links", [])
        
    except Exception as e:
        logger.error(f"Error analyzing links: {e}")
        return []




def generate_brochure_stream(website_data: Dict, llm_interface: LLMInterface) -> Generator[str, None, None]:
    """Generate brochure content by streaming from LLM."""
    try:
        # Get relevant links
        relevant_links = get_relevant_links(website_data, llm_interface)
        logger.info(f"Found {len(relevant_links)} relevant links")
        
        # Scrape additional pages
        additional_pages = []
        for link in relevant_links[:3]:  # Limit to 3 additional pages
            try:
                page_data = scrape_website(link["url"])
                page_data["type"] = link["type"]
                additional_pages.append(page_data)
            except Exception as e:
                logger.warning(f"Failed to scrape {link['url']}: {e}")
        
        # Generate brochure
        system_prompt = get_brochure_system_prompt()
        user_prompt = get_brochure_user_prompt(website_data, additional_pages)
        
        yield "# Generating Brochure...\n\n"
        
        for chunk in llm_interface.query_stream(user_prompt, system_prompt):
            yield chunk
            
    except Exception as e:
        logger.error(f"Error generating brochure: {e}")
        yield f"# Error\n\nAn error occurred while generating the brochure: {str(e)}"


class BrochureUI:
    """Gradio interface for the brochure generator."""
    
    def __init__(self):
        self.available_models = list(MODEL_CONFIGS.keys())
        self.interface = self._create_interface()
    
    def _create_interface(self) -> gr.Interface:
        """Create the Gradio interface with streaming support."""
        return gr.Interface(
            fn=self.generate_brochure_stream_ui,
            inputs=[
                gr.Dropdown(
                    choices=self.available_models,
                    value="openai",
                    label="Select LLM Model",
                    info="Choose which AI model to use for brochure generation"
                ),
                gr.Textbox(
                    label="Website URL",
                    placeholder="https://example.com",
                    info="Enter the URL of the website to generate a brochure for"
                )
            ],
            outputs=gr.Markdown(
                label="Generated Brochure",
                show_copy_button=True
            ),
            title="Website Brochure Generator",
            description="Generate professional brochures from any website using AI",
            theme=gr.themes.Soft(),
            flagging_mode="never"
        )
    
    def generate_brochure_stream_ui(self, model: str, url: str):
        """Streaming UI function for brochure generation."""
        try:
            # Validate inputs
            if not url.strip():
                yield "# Error\n\nPlease provide a valid website URL."
                return
            
            if not validate_url(url):
                yield "# Error\n\nPlease provide a valid URL (must start with http:// or https://)."
                return
            
            # Initialize LLM interface
            llm_interface = LLMInterface(model)
            
            # Scrape main website
            website_data = scrape_website(url)
            if website_data.get("status") == "error":
                yield f"# Error\n\nFailed to scrape website: {website_data.get('error', 'Unknown error')}"
                return
            
            # Generate brochure content with streaming
            result = ""
            for chunk in generate_brochure_stream(website_data, llm_interface):
                result += chunk
                yield result
                
        except ValueError as e:
            yield f"# Error\n\nConfiguration error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error in UI: {e}")
            yield f"# Error\n\nAn unexpected error occurred: {str(e)}"
    
    
    def launch(self, **kwargs):
        """Launch the Gradio interface."""
        return self.interface.launch(**kwargs)


def create_brochure_app() -> BrochureUI:
    """Create and return the brochure generator application."""
    return BrochureUI()


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Create and launch the app
    app = create_brochure_app()
    app.launch(share=True, server_name="0.0.0.0")