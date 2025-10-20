from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from openai import OpenAI


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

# Initialize OpenAI client for Ollama
ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # Ollama doesn't need a real API key
)


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]


def fetch_website_links(url):
    """
    Return the links on the webiste at the given url
    I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
    Feel free to use a class and optimize it!
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]


class WebsiteWithSelenium:
    """
    Enhanced Website class that can handle both static and JavaScript-rendered pages.
    Falls back to Selenium when minimal content is detected.
    """
    
    def __init__(self, url, use_selenium=False):
        """
        Create this Website object from the given url.
        If use_selenium is True, or if minimal content is detected, use Selenium.
        """
        self.url = url
        self.title = None
        self.text = None
        
        # Try regular requests first (unless explicitly told to use Selenium)
        if not use_selenium:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                self.title = soup.title.string if soup.title else "No title found"
                
                # Remove irrelevant elements
                if soup.body:
                    for irrelevant in soup.body(["script", "style", "img", "input"]):
                        irrelevant.decompose()
                    text = soup.body.get_text(separator="\n", strip=True)
                else:
                    text = ""
                
                # Check if content is minimal (likely JS-rendered)
                if len(text) < 500:  # Arbitrary threshold
                    print(f"⚠️ Minimal content ({len(text)} chars) - using Selenium to render JavaScript...")
                    use_selenium = True
                else:
                    self.text = text
                    print(f"✓ Fetched {len(self.text)} characters using requests")
                    return  # Successfully got content, no need for Selenium
            except Exception as e:
                print(f"⚠️ Error with requests: {e}")
                print(f"   Falling back to Selenium...")
                use_selenium = True
        
        # Use Selenium if needed
        if use_selenium:
            self._fetch_with_selenium()
    
    def _fetch_with_selenium(self):
        """
        Fetch the website content using Selenium with a headless Chrome browser.
        """
        # Configure Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"user-agent={headers['User-Agent']}")
        
        # Initialize the Chrome driver
        driver = None
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Load the page
            driver.get(self.url)
            
            # Wait for the page to load (wait for body to be present)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Give JavaScript time to render
            time.sleep(2)
            
            # Get the page source after JavaScript has rendered
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract title
            self.title = soup.title.string if soup.title else "No title found"
            
            # Remove irrelevant elements
            if soup.body:
                for irrelevant in soup.body(["script", "style", "img", "input"]):
                    irrelevant.decompose()
                self.text = soup.body.get_text(separator="\n", strip=True)
            else:
                self.text = soup.get_text(separator="\n", strip=True)
            
            print(f"✓ Fetched {len(self.text)} characters using Selenium")
            
        except Exception as e:
            print(f"Error with Selenium: {e}")
            self.title = "Error loading page"
            self.text = f"Could not load content from {self.url}"
        
        finally:
            if driver:
                driver.quit()
    
    def summarize(self, model="deepseek-r1:1.5b"):
        """
        Summarize the website content using DeepSeek-R1:1.5b model via Ollama.
        Returns a markdown-formatted summary.
        
        Args:
            model (str): The Ollama model to use. Default is "deepseek-r1:1.5b"
        
        Returns:
            str: The summary in markdown format
        """
        if not self.text:
            return "Error: No content to summarize. Please fetch the website first."
        
        system_prompt = """You are an assistant that analyzes the contents of a website 
and provides a short summary, ignoring text that might be navigation related. 
Respond in markdown."""
        
        user_prompt = f"""You are looking at a website titled {self.title}
The contents of this website is as follows; 
please provide a short summary of this website in markdown. 
If it includes news or announcements, then summarize these too.

{self.text}"""
        
        try:
            response = ollama_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating summary: {e}\nMake sure Ollama is running and the model '{model}' is installed."


def fetch_website_contents_selenium(url, use_selenium=False):
    """
    Return the title and contents of the website at the given url using the enhanced WebsiteWithSelenium class.
    Automatically detects when Selenium is needed, or you can force it with use_selenium=True.
    Truncate to 2,000 characters as a sensible limit.
    """
    website = WebsiteWithSelenium(url, use_selenium=use_selenium)
    return (website.title + "\n\n" + website.text)[:2_000]


def summarize_website(url, use_selenium=False, model="deepseek-r1:1.5b"):
    """
    Fetch and summarize a website using DeepSeek-R1:1.5b model via Ollama.
    
    Args:
        url (str): The website URL to fetch and summarize
        use_selenium (bool): Force Selenium usage (default: auto-detect)
        model (str): The Ollama model to use (default: "deepseek-r1:1.5b")
    
    Returns:
        str: The summary in markdown format
    
    Example:
        >>> summary = summarize_website("https://edwarddonner.com")
        >>> print(summary)
    """
    website = WebsiteWithSelenium(url, use_selenium=use_selenium)
    return website.summarize(model=model)
