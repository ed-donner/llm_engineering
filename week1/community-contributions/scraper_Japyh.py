from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents_selenium(url, wait_time=3):
    """
    Fetch website contents using Selenium to handle JavaScript-rendered pages
    """
    # Set up Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"user-agent={headers['User-Agent']}")
    
    driver = None
    try:
        # Initialize the Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Load the page
        driver.get(url)
        
        # Wait for the page to load (you can adjust this)
        time.sleep(wait_time)
        
        # Optionally wait for body to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Get the page source after JavaScript has rendered
        page_source = driver.page_source
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(page_source, "html.parser")
        
        # Extract title
        title = soup.title.string if soup.title else "No title found"
        
        # Extract text content
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input", "noscript"]):
                irrelevant.decompose()
            text = soup.body.get_text(separator="\n", strip=True)
        else:
            text = ""
        
        return (title + "\n\n" + text)[:2_000]
    
    except Exception as e:
        print(f"Selenium error: {e}")
        return None
    
    finally:
        if driver:
            driver.quit()


def fetch_website_contents_simple(url):
    """
    Simple fetch using requests (fallback method)
    """
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        title = soup.title.string if soup.title else "No title found"
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            text = soup.body.get_text(separator="\n", strip=True)
        else:
            text = ""
        return (title + "\n\n" + text)[:2_000]
    except Exception as e:
        print(f"Simple fetch error: {e}")
        return None


def fetch_website_contents(url, use_selenium=True):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit.
    
    Args:
        url: The URL to fetch
        use_selenium: If True, use Selenium for JavaScript rendering (default: True)
    
    Returns:
        String with title and content of the website
    """
    if use_selenium:
        # Try Selenium first for JavaScript-heavy sites
        result = fetch_website_contents_selenium(url)
        if result:
            return result
        else:
            print("Selenium failed, falling back to simple fetch...")
    
    # Fallback to simple requests
    result = fetch_website_contents_simple(url)
    if result:
        return result
    else:
        return "Error: Could not fetch website contents"


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
            return [link for link in links if link]
        
        except Exception as e:
            print(f"Selenium error fetching links: {e}")
            print("Falling back to simple fetch...")
        
        finally:
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
