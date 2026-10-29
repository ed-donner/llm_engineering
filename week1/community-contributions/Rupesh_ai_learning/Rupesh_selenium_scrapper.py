from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def fetch_website_contents_rp(url):
    """
    Return the title and contents of a website using Selenium.
    Truncate the result to 2,000 characters.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)

        WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )


        # Get the rendered HTML
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        title = soup.title.get_text(strip=True) if soup.title else "No title found"

        if soup.body:
            for irrelevant in soup.body(
                [ "script", "style", "img", "input", "nav", "header", "footer", "aside", "form", "button", "svg" ]
            ):
                irrelevant.decompose()

            text = soup.body.get_text(separator="\n", strip=True)
        else:
            text = ""

        website_content = (title + "\n\n" + text)[:2000]

        print("Scraped website title:", title)
        print("Scraped content length:", len(website_content))
        print("Scraped content preview:", website_content[:500])

        return website_content

    finally:
        driver.quit()
