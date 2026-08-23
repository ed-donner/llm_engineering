from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from webdriver_manager.chrome import ChromeDriverManager

def scrape_website(url):
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        wait = WebDriverWait(driver, 40)
        driver.get(url)
        time.sleep(10)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, features='html.parser')
        title = soup.title.string if soup.title else "No title found"
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            text = soup.body.get_text(separator="\n", strip=True)
        else:
            text = ""
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

    return (title + "\n\n" + text)[:2_000]

if __name__ == "__main__":
    url = "https://openai.com/about/"
    print(scrape_website(url))
