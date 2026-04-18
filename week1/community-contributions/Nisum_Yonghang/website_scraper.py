from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class Website:
    def __init__(self, url, wait_for_user=True, wait_time=10):
        self.url = url

        # Setup Chrome options
        options = Options()
        # options.add_argument("--headless")  # enable if you don't want browser UI
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service()
        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.get(url)

            # Optional manual verification
            if wait_for_user:
                input("Complete verification in browser, then press Enter...")

            # Optional auto wait fallback
            else:
                import time
                time.sleep(wait_time)

            page_source = driver.page_source

        finally:
            driver.quit()

        soup = BeautifulSoup(page_source, "html.parser")

        self.title = soup.title.string if soup.title else "No title found"

        # Remove junk tags
        for tag in soup(["script", "style", "img", "input"]):
            tag.decompose()

        self.text = soup.get_text(separator="\n", strip=True)
def scrape_website(url, wait_for_user=True):
    return Website(url, wait_for_user=wait_for_user)