# NEW SELENIUM SCRAPER IMPLEMENTATION

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
# import requests


def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=options)

def fetch_website_contents(url, driver=None):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
    """
    own_driver = driver is None
    if own_driver:
        driver = get_driver()

    driver.get(url)
    time.sleep(2)  # give JS time to render; swap for an explicit wait if needed

    soup = BeautifulSoup(driver.page_source, "html.parser")

    if own_driver:
        driver.quit()

    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]


def fetch_website_links(url, driver=None):
    """
    Return the links on the website at the given url
    """
    own_driver = driver is None
    if own_driver:
        driver = get_driver()

    driver.get(url)
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    if own_driver:
        driver.quit()

    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]


# PREVIOUS DEFAULT IMPLEMENTATION W/ BEAUTIFULSOUP

# Standard headers to fetch a website
# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
# }


# def fetch_website_contents(url):
#     """
#     Return the title and contents of the website at the given url;
#     truncate to 2,000 characters as a sensible limit
#     """
#     response = requests.get(url, headers=headers)
#     soup = BeautifulSoup(response.content, "html.parser")
#     title = soup.title.string if soup.title else "No title found"
#     if soup.body:
#         for irrelevant in soup.body(["script", "style", "img", "input"]):
#             irrelevant.decompose()
#         text = soup.body.get_text(separator="\n", strip=True)
#     else:
#         text = ""
#     return (title + "\n\n" + text)[:2_000]


# def fetch_website_links(url):
#     """
#     Return the links on the webiste at the given url
#     I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
#     Feel free to use a class and optimize it!
#     """
#     response = requests.get(url, headers=headers)
#     soup = BeautifulSoup(response.content, "html.parser")
#     links = [link.get("href") for link in soup.find_all("a")]
#     return [link for link in links if link]
