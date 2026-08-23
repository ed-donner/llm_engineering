from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv(override=True)

# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_content(url, max_chars=2000, use_selenium=True):
    """
    Fetch raw website content without AI summarization.
    
    Args:
        url: The URL to fetch
        max_chars: Maximum characters to return (default: 2000)
        use_selenium: Whether to try Selenium first (default: True)
    
    Returns:
        String with title and content of the website, truncated to max_chars
    """
    
    # Method 1: Try Selenium (for JavaScript-rendered sites)
    if use_selenium:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"user-agent={headers['User-Agent']}")
        
        driver = None
        try:
            # Initialize Chrome driver
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get rendered HTML
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            
            # Extract title
            title = soup.title.string if soup.title else "No title found"
            
            # Extract and clean text
            if soup.body:
                for irrelevant in soup.body(["script", "style", "img", "input", "noscript"]):
                    irrelevant.decompose()
                text = soup.body.get_text(separator="\n", strip=True)
            else:
                text = ""
            
            driver.quit()
            return (title + "\n\n" + text)[:max_chars]
        
        except Exception as e:
            print(f"Selenium failed ({e}), falling back to simple requests...")
            if driver:
                driver.quit()
    
    # Method 2: Fallback to simple requests + BeautifulSoup
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extract title
        title = soup.title.string if soup.title else "No title found"
        
        # Extract and clean text
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            text = soup.body.get_text(separator="\n", strip=True)
        else:
            text = ""
        
        return (title + "\n\n" + text)[:max_chars]
    
    except Exception as e:
        return f"Error: Could not fetch website contents - {e}"


def summarize_website(url, model="gpt-4.1-mini", max_chars=2000, use_selenium=True):
    """
    Smart website scraper with AI-powered summarization.
    Fetches website content and generates a summary using specified AI model.
    
    Args:
        url: The URL to fetch and summarize
        model: AI model to use for summarization (default: "gpt-4.1-mini")
               Examples: "gpt-4.1-mini", "gpt-4.1-nano", "llama3.2:1b", "llama3.2:3b"
        max_chars: Maximum characters to fetch from website (default: 2000)
        use_selenium: Whether to try Selenium first (default: True)
    
    Returns:
        AI-generated summary of the website content in markdown format
    """
    
    # Step 1: Fetch the website content
    website_content = fetch_website_content(url, max_chars=max_chars, use_selenium=use_selenium)
    
    if website_content.startswith("Error:"):
        return website_content
    
    # Step 2: Prepare the prompts for AI summarization
    system_prompt = """
You are a helpful assistant that analyzes website contents and provides clear, 
concise summaries. Focus on the main purpose, key information, and any important 
announcements or features. Respond in markdown format.
"""
    
    user_prompt = f"""
Here are the contents of a website:

{website_content}

Please provide a clear and concise summary of this website, including:
1. The main purpose or focus
2. Key features or offerings
3. Any important news or announcements

Format your response in markdown.
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Step 3: Call the AI model
    try:
        # Check if it's an Ollama model (contains colon like "llama3.2:1b")
        if ":" in model or model.startswith("llama") or model.startswith("mistral"):
            # Use Ollama
            client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama"  # Ollama doesn't need a real API key
            )
        else:
            # Use OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error generating summary with model '{model}': {e}\n\nRaw content:\n{website_content}"



# Legacy function names for backward compatibility
def fetch_website_contents(url, use_selenium=True):
    """
    Legacy function name - calls fetch_website_content.
    Kept for backward compatibility with existing code.
    Returns raw content without AI summarization.
    """
    return fetch_website_content(url, max_chars=2000, use_selenium=use_selenium)


def fetch_website_links(url, use_selenium=True):
    """
    Return the links on the website at the given url.
    Uses Selenium by default to handle JavaScript-rendered content.
    
    Args:
        url: The URL to fetch
        use_selenium: If True, use Selenium for JavaScript rendering (default: True)
    
    Returns:
        List of links found on the page
    """
    if use_selenium:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={headers['User-Agent']}")
        
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            time.sleep(2)  # Wait for page to load
            
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            links = [link.get("href") for link in soup.find_all("a")]
            
            if driver:
                driver.quit()
            
            return [link for link in links if link]
        
        except Exception as e:
            print(f"Selenium error fetching links: {e}")
            print("Falling back to simple fetch...")
            if driver:
                driver.quit()
    
    # Fallback to simple requests
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        links = [link.get("href") for link in soup.find_all("a")]
        return [link for link in links if link]
    except Exception as e:
        print(f"Error fetching links: {e}")
        return []
