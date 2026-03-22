from bs4 import BeautifulSoup
import requests
import re
import time
from typing import Dict, List, Set
from urllib.parse import urljoin

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

_CAPTCHA_MARKERS = [
    "captcha-delivery.com",
    "please enable js",
    "disable any ad blocker",
    "cloudflare",
]


def _decode_embedded_escaped_text(s: str) -> str:
    """
    Decode strings like `http:\\u002F\\u002Fexample.com\\u002F` that show up in
    embedded JSON inside HTML.
    """
    if not s:
        return s

    # Commonly seen escape pattern for forward slashes.
    s = s.replace("\\/", "/")

    def _sub_u(match: re.Match[str]) -> str:
        codepoint = int(match.group(1), 16)
        return chr(codepoint)

    # Decode both `\\uXXXX` and `\uXXXX`-style escapes.
    s = re.sub(r"\\\\u([0-9a-fA-F]{4})", _sub_u, s)
    s = re.sub(r"\\u([0-9a-fA-F]{4})", _sub_u, s)
    return s


def _tripadvisor_page_url(base_url: str, offset: int) -> str:
    """
    TripAdvisor restaurant/category listings paginate with a "-oa{offset}" suffix.

    Example:
      https://www.tripadvisor.com/Restaurants-...html
      https://www.tripadvisor.com/Restaurants-...-oa30.html
    """
    # Split query/fragment so we don't accidentally insert "-oa{offset}" into them.
    url_no_fragment, fragment = (base_url.split("#", 1) + [""])[:2]
    url_no_query, query = (url_no_fragment.split("?", 1) + [""])[:2]

    if offset == 0:
        # Remove any existing "-oa<number>" so page 0 stays canonical.
        url_no_oa = re.sub(r"-oa\d+", "", url_no_query)
        return f"{url_no_oa}{('?' + query) if query else ''}{('#' + fragment) if fragment else ''}"

    # If "-oa<number>" already exists, replace it; otherwise inject before ".html".
    if re.search(r"-oa\d+", url_no_query):
        new_url = re.sub(r"-oa\d+", f"-oa{offset}", url_no_query)
    elif url_no_query.endswith(".html"):
        new_url = re.sub(r"\.html$", f"-oa{offset}.html", url_no_query)
    else:
        new_url = f"{url_no_query}-oa{offset}"

    return f"{new_url}{('?' + query) if query else ''}{('#' + fragment) if fragment else ''}"


def fetch_tripadvisor_restaurants(
    url: str,
    *,
    max_pages: int = 50,
    sleep_seconds: float = 1.0,
    retries: int = 3,
    backoff_seconds: float = 5.0,
) -> List[Dict[str, str]]:
    """
    Fetch restaurant listings from a TripAdvisor restaurants landing page.

    Args:
        url: Base listing page URL (e.g. the Islamabad restaurants page).
        max_pages: Safety cap on how many pages to request (page size is ~30 per TripAdvisor).
        sleep_seconds: Delay between requests to be polite / reduce rate limiting.

    Returns:
        A list of dicts: {"name": <restaurant name>, "url": <absolute restaurant review url>}.

    Notes:
        - TripAdvisor HTML can change; this scraper focuses on extracting links to
          pages containing "/Restaurant_Review".
        - Results are deduplicated by restaurant URL.
    """
    restaurant_urls_seen: Set[str] = set()
    restaurants: List[Dict[str, str]] = []
    session = requests.Session()
    session.headers.update(headers)

    # TripAdvisor listings are typically paginated by increments of 30.
    page_size = 30

    for page_idx in range(max_pages):
        offset = page_idx * page_size
        page_url = _tripadvisor_page_url(url, offset)

        response = None
        last_error = None
        for attempt in range(retries):
            try:
                response = session.get(page_url, timeout=30)
                if response.status_code in (403, 429, 503):
                    time.sleep(backoff_seconds * (attempt + 1))
                    continue
                response.raise_for_status()
                last_error = None
                break
            except Exception as e:
                last_error = e
                time.sleep(backoff_seconds * (attempt + 1))

        if response is None:
            raise last_error or RuntimeError("Failed to fetch TripAdvisor page")

        page_text = ""
        try:
            page_text = response.text or ""
        except Exception:
            page_text = ""

        lowered = page_text.lower()
        if any(marker in lowered for marker in _CAPTCHA_MARKERS):
            raise RuntimeError(
                "TripAdvisor blocked the scraper (captcha/JS challenge). "
                "Use a browser-based scraper (Playwright/Selenium) if you must."
            )

        soup = BeautifulSoup(response.content, "html.parser")

        # Restaurant cards link to ".../Restaurant_Review-<id>-...".
        link_elems = soup.find_all("a", href=True)
        page_new_count = 0

        for a in link_elems:
            href = a.get("href")
            if not href:
                continue

            abs_url = urljoin("https://www.tripadvisor.com", href)
            if "/Restaurant_Review" not in abs_url:
                continue

            if abs_url in restaurant_urls_seen:
                continue

            # Try a couple common places for the human-readable name.
            name = (a.get_text(strip=True) or a.get("title") or "").strip()

            if not name:
                # Fallback: if anchor text is empty, try to locate nearby text.
                # We keep this conservative to avoid pulling in nav/header strings.
                parent = a.parent
                if parent:
                    name = parent.get_text(" ", strip=True)

            # Basic cleanup; don't assume the full string is the name.
            name = re.sub(r"\s+", " ", name).strip()

            restaurant_urls_seen.add(abs_url)
            restaurants.append({"name": name or "Unknown", "url": abs_url})
            page_new_count += 1

        # Fallback: if the HTML doesn't contain the usual `/Restaurant_Review`
        # anchors, sometimes the response is an embedded JSON payload where
        # each place includes a `name` plus a link-like field (e.g. `website`
        # or `sources[].url`).
        if page_new_count == 0 and page_text:
            place_name_re = re.compile(
                r'"id"\s*:\s*\d+\s*,\s*"name"\s*:\s*"([^"]+)"\s*,\s*"placePageType"\s*:\s*"visible"',
                re.IGNORECASE,
            )

            for m in place_name_re.finditer(page_text):
                raw_name = m.group(1)
                name = _decode_embedded_escaped_text(raw_name).strip()
                if not name:
                    continue

                # Take a limited window around the match and look for a URL.
                chunk = page_text[m.start() : m.start() + 5000]

                url_match = re.search(r'"website"\s*:\s*"([^"]+)"', chunk)
                if not url_match:
                    url_match = re.search(
                        r'"sources"\s*:\s*\[\s*\{\s*[^}]*?"url"\s*:\s*"([^"]+)"',
                        chunk,
                        flags=re.IGNORECASE,
                    )
                if not url_match:
                    continue

                raw_url = url_match.group(1)
                decoded_url = _decode_embedded_escaped_text(raw_url).strip()
                if not decoded_url or decoded_url.lower() == "null":
                    continue

                if not (decoded_url.startswith("http://") or decoded_url.startswith("https://")):
                    continue

                if decoded_url in restaurant_urls_seen:
                    continue

                restaurant_urls_seen.add(decoded_url)
                restaurants.append({"name": name or "Unknown", "url": decoded_url})
                page_new_count += 1

        # Stop early once pages stop producing new restaurants.
        if page_idx > 0 and page_new_count == 0:
            break

        if sleep_seconds:
            time.sleep(sleep_seconds)

    return restaurants