from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def _build_driver() -> webdriver.Chrome:
    """Configure a headless Chrome instance."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def fetch_website_contents_selenium(url,  wait_seconds: int = 10):
    """
    Load a URL in a headless browser, wait for the page to render,
    and return the visible text content of the body.

    Works on JavaScript-rendered sites (React, Vue, etc.) that the
    plain requests-based scraper can't see.
    """
    driver = _build_driver()

    try:
        driver.get(url)

        # Wait until the <body> tag is present before reading content
        WebDriverWait(driver, wait_seconds).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        body = driver.find_element(By.TAG_NAME, "body")
        text = body.text

        return text.strip()

    finally:
        driver.quit()

