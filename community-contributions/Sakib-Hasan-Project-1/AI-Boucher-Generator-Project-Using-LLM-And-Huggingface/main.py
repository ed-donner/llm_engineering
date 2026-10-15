import requests

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


# ============================================================
# IMPORTANT KEYWORDS
# ============================================================

IMPORTANT_KEYWORDS = [
    "about",
    "product",
    "service",
    "solution",
    "contact",
    "company",
    "team",
    "mission",
    "career",
    "application",
    "technology",
]


# ============================================================
# REQUEST HEADERS
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,"
        "image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ============================================================
# NORMALIZE URL
# ============================================================

def normalize_url(url):

    url = url.strip()

    if not url:
        raise ValueError(
            "Website URL cannot be empty."
        )

    if not url.startswith(
        ("http://", "https://")
    ):
        url = "https://" + url

    return url


# ============================================================
# SCRAPE WEBSITE
# ============================================================

def scrape_website(url):

    # --------------------------------------------------------
    # STEP 1 — Normalize URL
    # --------------------------------------------------------

    url = normalize_url(url)

    print("Scraping URL:", url)


    # --------------------------------------------------------
    # STEP 2 — Send HTTP Request
    # --------------------------------------------------------

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
            allow_redirects=True
        )

    except requests.exceptions.Timeout:

        raise RuntimeError(
            "Website request timed out. "
            "The website took too long to respond."
        )

    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            "Could not connect to the website. "
            "Please check the URL."
        )

    except requests.exceptions.RequestException as e:

        raise RuntimeError(
            f"Website request failed: {e}"
        )


    # --------------------------------------------------------
    # STEP 3 — Check HTTP Status
    # --------------------------------------------------------

    print(
        "Status Code:",
        response.status_code
    )

    if not 200 <= response.status_code < 300:

        raise RuntimeError(
            f"Website returned HTTP "
            f"{response.status_code}."
        )


    # --------------------------------------------------------
    # STEP 4 — Parse HTML
    # --------------------------------------------------------

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    # --------------------------------------------------------
    # STEP 5 — Remove Unnecessary Elements
    # --------------------------------------------------------

    for element in soup(
        ["script", "style", "noscript"]
    ):
        element.decompose()


    # --------------------------------------------------------
    # STEP 6 — Find Base Domain
    # --------------------------------------------------------

    base_domain = urlparse(
        response.url
    ).netloc.lower()

    print(
        "Final URL:",
        response.url
    )

    print(
        "Base domain:",
        base_domain
    )


    # ========================================================
    # TITLE
    # ========================================================

    title = ""

    if soup.title:

        title = soup.title.get_text(
            strip=True
        )


    # ========================================================
    # HEADINGS
    # ========================================================

    headings = []

    for heading in soup.find_all(
        ["h1", "h2", "h3"]
    ):

        text = heading.get_text(
            " ",
            strip=True
        )

        if text:

            headings.append(text)


    # ========================================================
    # PARAGRAPHS
    # ========================================================

    paragraphs = []

    for paragraph in soup.find_all("p"):

        text = paragraph.get_text(
            " ",
            strip=True
        )

        if text:

            paragraphs.append(text)


    # ========================================================
    # IMPORTANT INTERNAL LINKS
    # ========================================================

    important_links = []

    for link in soup.find_all(
        "a",
        href=True
    ):

        href = link.get("href", "").strip()

        text = link.get_text(
            " ",
            strip=True
        )


        if not href:

            continue


        # Convert relative URL to absolute URL

        full_url = urljoin(
            response.url,
            href
        )


        # Get domain

        link_domain = urlparse(
            full_url
        ).netloc.lower()


        # Only internal links

        if (
            text
            and link_domain == base_domain
        ):

            link_content = (
                text + " " + full_url
            ).lower()


            is_important = any(
                keyword in link_content
                for keyword in IMPORTANT_KEYWORDS
            )


            if is_important:

                important_links.append(
                    {
                        "text": text,
                        "url": full_url
                    }
                )


    # ========================================================
    # REMOVE DUPLICATE LINKS
    # ========================================================

    unique_links = []

    seen_urls = set()

    for link in important_links:

        if link["url"] not in seen_urls:

            unique_links.append(link)

            seen_urls.add(
                link["url"]
            )


    # ========================================================
    # LIMIT DATA
    # ========================================================

    # Prevent extremely large websites from sending
    # too much data to the LLM.

    headings = headings[:50]

    paragraphs = paragraphs[:100]

    unique_links = unique_links[:50]


    # ========================================================
    # FINAL SCRAPED DATA
    # ========================================================

    scraped_data = {

        "website": response.url,

        "title": title,

        "headings": headings,

        "paragraphs": paragraphs,

        "important_links": unique_links

    }


    # ========================================================
    # DEBUG INFORMATION
    # ========================================================

    print(
        "Title:",
        title
    )

    print(
        "Headings:",
        len(headings)
    )

    print(
        "Paragraphs:",
        len(paragraphs)
    )

    print(
        "Important links:",
        len(unique_links)
    )


    # ========================================================
    # BASIC CONTENT CHECK
    # ========================================================

    if not title and not headings and not paragraphs:

        raise RuntimeError(
            "The website returned HTML, "
            "but no useful content could be extracted. "
            "The website may require JavaScript."
        )


    return scraped_data