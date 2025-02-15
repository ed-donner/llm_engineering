# -*- coding: utf-8 -*-

# Author Philine Huß
# Datum: 11.02.2025

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.keys import Keys
import time

service = Service(executable_path=r'C:\Program Files\BrowserDrivers\geckodriver.exe')
print(service)


driver = webdriver.Firefox(service=service)
driver.get('https://be-able.info/de/be-able/')

# Find first paragraph p on the page
element = driver.find_element(By.TAG_NAME, "p")
print(element.text)


# Find all paragraphs p on the page
def find_paragraphs_on_page():
    elements = driver.find_elements(By.TAG_NAME, "p")
    for ele in elements:
        print(ele.text)


def dismiss_cookie():
    try:
        cookie = driver.find_element(
            By.CSS_SELECTOR, '[role="dialog"][aria-label="cookieconsent"]'
        )
        dismiss_button = driver.find_element(
            By.CLASS_NAME, 'cc-btn.cc-dismiss')
        dismiss_button.click()
        print("Cookie Banner clicked away")
    except Exception as e:
        print(f"Error dismissing cookie banner: {e}")

dismiss_cookie()

# Find all paragraphs p on all pages of website by iterating to all links on
# home page. "a" is tag name for links
links = driver.find_elements(By.TAG_NAME, "a")
print("Iterating through links...\n")
for link in links:
    try:
        href = link.get_attribute("href")

        if href and not "cookie" in href:
            print(f"Navigating to subpage: {href}")
            driver.get(href)
            time.sleep(2)  # Wait for page to load
            find_paragraphs_on_page()
    except Exception as e:
        print(f"Error navigating to link {e}")


driver.quit()


def main():
    pass


if __name__ == '__main__':
    main()
