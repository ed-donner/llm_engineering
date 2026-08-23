from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def get_headless_driver():
    """
    Configures and returns a headless Chrome browser.
    """
    options = Options()
    options.add_argument("--headless=new")  # Runs Chrome in the background without UI
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    )
    
    driver = webdriver.Chrome(options=options)
    return driver


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url,
    using Selenium to execute JavaScript. Truncates to 2,000 characters.
    """
    driver = get_headless_driver()
    try:
        driver.get(url)
        # Give JS frameworks a moment to hydrate/render content
        time.sleep(2)
        
        # Extract the fully rendered HTML source
        html_content = driver.page_source
    finally:
        driver.quit()

    soup = BeautifulSoup(html_content, "html.parser")
    
    title = soup.title.string if soup.title and soup.title.string else "No title found"
    
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
        
    return (title + "\n\n" + text)[:2_000]


def fetch_website_links(url):
    """
    Return the links on the website at the given url using Selenium.
    """
    driver = get_headless_driver()
    try:
        driver.get(url)
        time.sleep(2)
        html_content = driver.page_source
    finally:
        driver.quit()

    soup = BeautifulSoup(html_content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]

if __name__ == "__main__":
    test_url = "https://openai.com"

    print("Fetching website contents...")
    content = fetch_website_contents(test_url)
    print("\n--- CONTENT PREVIEW ---")
    print(content)

    print("\nFetching website links...")
    links = fetch_website_links(test_url)
    print("\n--- FOUND LINKS (First 10) ---")
    print(links[:10])