# BeautifulSoup is a library for parsing (reading/navigating) HTML content
from bs4 import BeautifulSoup
# requests is a library that lets us make HTTP requests (like visiting a website)
import requests


# Websites often block automated requests, so we mimic a real browser by sending
# these "headers" along with our request. The User-Agent string identifies us
# as a Chrome browser on Windows, which most sites will accept.
# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    """
    Return the title and contents of the website at the given url;
    truncate to 2,000 characters as a sensible limit
    """
    # Send a GET request to the URL (like typing it into a browser) and store the response
    response = requests.get(url, headers=headers)
    # Parse the raw HTML bytes from the response into a navigable tree structure.
    # "html.parser" is Python's built-in HTML parser — no extra install needed.
    soup = BeautifulSoup(response.content, "html.parser")
    # Try to find the <title> tag and grab its text. If there's no title tag,
    # fall back to the string "No title found" using a conditional expression (ternary).
    title = soup.title.string if soup.title else "No title found"

    # Check if the page has a <body> tag — most pages do, but some minimal ones don't
    if soup.body:
        # Loop over all tags we don't care about (scripts, styles, images, form inputs)
        # and remove them entirely from the parsed tree so they don't pollute our text
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()  # .decompose() deletes the tag and all its contents

        # Extract all remaining visible text from the body.
        # separator="\n" puts each block of text on its own line,
        # strip=True removes leading/trailing whitespace from each piece.
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        # If there's no body at all, just return an empty string
        text = ""

    # Combine the title and body text, then slice to the first 2,000 characters.
    # The underscore in 2_000 is just a readability separator — Python ignores it.
    return (title + "\n\n" + text)[:2_000]

def fetch_website_links(url):
    """
    Return the links on the webiste at the given url
    I realize this is inefficient as we're parsing twice! This is to keep the code in the lab simple.
    Feel free to use a class and optimize it!
    """
    # Make the same GET request as above to download the page's HTML
    response = requests.get(url, headers=headers)

    # Parse the HTML into a BeautifulSoup tree, just like in the function above
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find every <a> (anchor/link) tag on the page, then extract the "href" attribute
    # from each one. href is the actual URL the link points to.
    # This is a list comprehension — a compact way to build a list with a loop.
    links = [link.get("href") for link in soup.find_all("a")]

    # Filter out any None values — .get("href") returns None if the tag has no href,
    # and "if link" skips any falsy values (None, empty string, etc.)
    return [link for link in links if link]
