from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def _make_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


class Website:
    """
    Drop-in replacement for the requests-based Website class.
    Uses Selenium to render JavaScript, so it works on sites that
    block simple HTTP scrapers or load content dynamically.
    """

    def __init__(self, url):
        self.url = url
        self.title = ""
        self.text = ""
        self.links = []

        driver = _make_driver()
        try:
            driver.get(url)
            # Wait until <body> is present before extracting HTML
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            html = driver.page_source
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            html = ""
        finally:
            driver.quit()

        if html:
            soup = BeautifulSoup(html, "html.parser")

            self.title = (
                soup.title.string.strip()
                if soup.title and soup.title.string
                else "No title found"
            )

            if soup.body:
                for tag in soup.body(["script", "style", "img", "input"]):
                    tag.decompose()
                self.text = soup.body.get_text(separator="\n", strip=True)

            self.links = [
                urljoin(url, link.get("href"))
                for link in soup.find_all("a")
                if link.get("href")
            ]

    def get_contents(self, limit=2000):
        return (self.title + "\n\n" + self.text)[:limit]

    def get_links(self):
        return self.links

    def __str__(self):
        return self.get_contents()


def fetch_website_contents(url):
    return Website(url)


if __name__ == "__main__":
    website = fetch_website_contents("https://example.com")
    print("TITLE:", website.title)
    print("\nCONTENT:")
    print(website.get_contents())
    print("\nLINKS:")
    for link in website.get_links():
        print(link)
