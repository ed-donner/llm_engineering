from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]


def fetch_website_links(url):
    """
    Return the links on the webiste at the given url
    I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
    Feel free to use a class and optimize it!
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]


def fetch_yahoo_top_losers(base_url="https://finance.yahoo.com/", limit=5):
    """
    Return the first `limit` tickers from Yahoo Finance's Top Losers table.

    Each result is a dictionary containing the ticker and its absolute quote URL.
    """
    losers_url = urljoin(base_url, "markets/stocks/losers/")
    response = requests.get(losers_url, headers=headers, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    losers = []
    seen_tickers = set()
    for row in soup.select("table tbody tr"):
        quote_link = row.select_one('a[href*="/quote/"]')
        if not quote_link:
            continue

        quote_url = urljoin(base_url, quote_link.get("href"))
        path_parts = urlparse(quote_url).path.strip("/").split("/")
        if len(path_parts) < 2 or path_parts[0] != "quote":
            continue

        ticker = path_parts[1].upper()
        if ticker in seen_tickers:
            continue

        losers.append({"ticker": ticker, "url": quote_url})
        seen_tickers.add(ticker)
        if len(losers) == limit:
            break

    if not losers:
        raise ValueError("Non è stato possibile trovare i ticker nella sezione Top Losers")

    return losers
