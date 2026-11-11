from selenium import webdriver
from selenium.webdriver.common.by import By


def fetch_website_contents(url):
    driver = webdriver.Chrome()
    try:
        driver.get(url)
        print(driver.title)
        body = driver.find_element(By.TAG_NAME, "body")
        return body.text[:2_000]  # Return the body text truncated to 2,000 characters
    finally:
        driver.quit()

    