import requests
from bs4 import BeautifulSoup

url = "https://www.iana.org/help/example-domains"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

def fetch_website_content(url):
    response = requests.get(url,headers=headers)
    html = response.text
    soup = BeautifulSoup(html,"html.parser")

    title = soup.title.text if soup.title else "No Title"

    if soup.body:
        for noneed in soup.body(["script","style","img","input"]):
            noneed.decompose()
        text = soup.body.get_text(separator="\n",strip=True)

    else:
        text = ""

    return (title +"\n\n" + text)[:2001]




