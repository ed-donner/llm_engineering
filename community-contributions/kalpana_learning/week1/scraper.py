from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def create_driver():
    options = Options()
    # options.add_argument("--headless=new")  # keep disabled while debugging
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=options)


def fetch_website_contents(url):
    driver = create_driver()

    try:
        driver.get(url)

        WebDriverWait(driver, 20).until(
            lambda d: d.find_element(By.TAG_NAME, "body")
        )

        time.sleep(5)

        print("Final URL:", driver.current_url)
        print("Page title:", driver.title)

        text = driver.find_element(By.TAG_NAME, "body").text.strip()

        # Detect common challenge/block pages
        blocked_keywords = [
            "enable javascript",
            "enable cookies",
            "javascript and cookies",
            "checking your browser",
            "verify you are human",
            "captcha",
            "access denied",
            "security check",
            "challenge"
        ]

        lower_text = text.lower()

        if any(keyword in lower_text for keyword in blocked_keywords):
            raise Exception(
                "Website could not be accessed normally. "
                "Selenium received a JavaScript/cookie/security challenge page."
            )

        if len(text) < 200:
            raise Exception(
                "Website returned too little readable content."
            )

        return (driver.title + "\n\n" + text)[:12000]

    finally:
        driver.quit()