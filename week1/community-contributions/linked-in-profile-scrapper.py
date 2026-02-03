# ===========================
# System & Environment
# ===========================
import os
from dotenv import load_dotenv

# ===========================
# Web Scraping
# ===========================
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ===========================
# AI-related
# ===========================
from IPython.display import Markdown, display
from openai import OpenAI
import ollama


load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

if not api_key:
   raise ValueError("OPENAI_API_KEY not found in environment variables")

print("✅ API key loaded successfully!")
openai = OpenAI()


class WebsiteCrawler:
    def __init__(self, url):
        self.url = url
        self.title = ""
        self.text = ""
        self.scrape()

    def scrape(self):
        try:
            # Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            # Try to find Chrome
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME')),
            ]

            chrome_binary = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_binary = path
                    break

            if chrome_binary:
                chrome_options.binary_location = chrome_binary

            # Create driver
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)

            print(f"🔍 Loading: {self.url}")
            driver.get(self.url)

            # Wait for page to load
            time.sleep(5)

            # Try to wait for main content
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
            except Exception:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                except Exception:
                    pass  # Continue anyway

            # Get title and page source
            self.title = driver.title
            page_source = driver.page_source
            driver.quit()

            print(f"✅ Page loaded: {self.title}")

            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')

            # Remove unwanted elements
            for element in soup(["script", "style", "img", "input", "button", "nav", "footer", "header"]):
                element.decompose()

            # Get main content
            main = soup.find('main') or soup.find('article') or soup.find('.content') or soup.find('body')
            if main:
                self.text = main.get_text(separator="\n", strip=True)
            else:
                self.text = soup.get_text(separator="\n", strip=True)

            # Clean up text
            lines = [line.strip() for line in self.text.split('\n') if line.strip() and len(line.strip()) > 2]
            self.text = '\n'.join(lines[:200])  # Limit to first 200 lines

            print(f"📄 Extracted {len(self.text)} characters")

        except Exception as e:
            print(f"❌ Error occurred: {e}")
            self.title = "Error occurred"
            self.text = "Could not scrape website content"



system_prompt = "You are a helpful assistant that can scrape a LinkedIn profile and extract the name, headline, location, and about section."

def user_prompt_for(url):
    user_prompt = f"You are looking at a LinkedIn profile at {url}"
    user_prompt += "\nThe contents of this LinkedIn profile is as follows; please provide a short summary of this LinkedIn profile in markdown. If it includes news or announcements, then summarize these too.\n\n"
    user_prompt += url.text
    return user_prompt


def scrape_linkedin(url):
    """Scrape LinkedIn profile and summarize with GPT"""
    website = WebsiteCrawler(url)
    response = openai.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_for(website)}
        ]
    )
    return response.choices[0].message.content


print(scrape_linkedin("https://www.linkedin.com/in/youssefwilliam/"))
