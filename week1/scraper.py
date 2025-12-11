import json
import os
import sys
import time

#region agent log
try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError as e:
    log_payload = {
        "sessionId": "debug-session",
        "runId": "pre-fix",
        "hypothesisId": "H1",
        "location": "week1/scraper.py:1",
        "message": "bs4 import failed",
        "data": {
            "sys_executable": sys.executable,
            "sys_path": sys.path,
            "cwd": os.getcwd(),
            "error": str(e),
        },
        "timestamp": int(time.time() * 1000),
    }
    with open("/Users/shuhuili/Documents/Projects/.cursor/debug.log", "a") as log_f:
        log_f.write(json.dumps(log_payload) + "\n")
    raise
#endregion

import requests


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
    """
#region agent log
    with open("/Users/shuhuili/Documents/Projects/.cursor/debug.log", "a") as log_f:
        log_f.write(
            json.dumps(
                {
                    "sessionId": "debug-session",
                    "runId": "pre-fix",
                    "hypothesisId": "H2",
                    "location": "week1/scraper.py:11",
                    "message": "fetch_website_contents entry",
                    "data": {"url": url},
                    "timestamp": int(time.time() * 1000),
                }
            )
            + "\n"
        )
#endregion
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
