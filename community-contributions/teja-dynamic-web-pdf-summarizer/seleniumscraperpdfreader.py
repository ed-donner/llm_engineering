import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pypdf
from io import BytesIO
from pypdf import PdfReader
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

def fetch_website_contents(url):
    #Step 1: static fetch of html content 
    html = fetch_html_static(url)
    soup = BeautifulSoup(html, "html.parser")
    text = extract_text_from_html(html)

    #Step 2: check for pdf in static html content
    pdf_url = find_pdf_url(soup, url)
    
    if pdf_url:
        print("PDF found in static HTML content")
        return extract_text_from_pdf(pdf_url)

    #Step 3: check for sparse content
    if is_content_sparse(text):
        print("Content is sparse, fetching dynamic content using Selenium")

        html = fetch_html_selenium(url)
        soup = BeautifulSoup(html, "html.parser")
        text = extract_text_from_html(html)

        #Step 4: check for pdf in dynamic html content
        pdf_url = find_pdf_url(soup, url)
        if pdf_url:
            print("PDF found in dynamic HTML content using Selenium")
            return extract_text_from_pdf(pdf_url)
    
    return text

def fetch_html_static(url):
    response = requests.get(url, headers=headers, timeout=10)
    return response.content

def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:5000]

def fetch_html_selenium(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options
        )
    driver.get(url)
    time.sleep(3)
    html_content = driver.page_source
    driver.quit()
    return html_content

def is_content_sparse(text, min_length=300):
    return len(text.strip()) < min_length


def fetch_website_links(url):
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]

def find_pdf_url(soup, base_url):
    for tag in soup.find_all(["a", "iframe", "embed", "object"]):
        url = tag.get("href") or tag.get("src") or tag.get("data")

        if url and ".pdf" in url.lower():
            return urljoin(base_url, url)
    return None

def extract_text_from_pdf(pdf_url):
    response = requests.get(pdf_url, headers=headers, timeout=10)
    pdf_file = BytesIO(response.content)
    try:
        reader = PdfReader(pdf_file)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text