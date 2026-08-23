import asyncio
from typing import TypedDict
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


class PageData(TypedDict):
    """Structured result returned by the scraper."""
    url: str
    title: str
    content: str


class Link(TypedDict):
    """A single hyperlink extracted from a page."""
    href: str
    text: str


class PageLinks(TypedDict):
    """Structured result returned by the link extractor."""
    url: str
    links: list[Link]


async def scrape_webpage(url: str, wait_for: str = "networkidle", timeout: int = 30000) -> PageData:
    """
    Scrape the title and text content of a webpage using Playwright.

    Playwright launches a real browser (Chromium by default), which fully executes
    JavaScript — making it ideal for React, Vue, Angular, and other JS-heavy sites
    that plain HTTP clients like `requests` cannot render.

    Args:
        url (str): The full URL of the webpage to scrape
                   (e.g. "https://example.com").
        wait_for (str): The condition to wait for before extracting content.
                        Options:
                          - "networkidle"      → waits until network has been idle
                                                 for 500ms (best for SPAs). [default]
                          - "domcontentloaded" → waits for the HTML to be parsed.
                          - "load"             → waits for the load event.
                          - "commit"           → waits until the response starts arriving.
        timeout (int): Maximum time in milliseconds to wait for the page to load.
                       Defaults to 30000 (30 seconds).

    Returns:
        PageData: A TypedDict containing:
            - ``url``     (str): The URL that was scraped.
            - ``title``   (str): The page's <title> tag value, or an empty string
                                 if no title was found.
            - ``content`` (str): The visible text content of the fully rendered
                                 page, with whitespace normalized.

    Raises:
        PlaywrightTimeoutError: If the page does not load within the timeout period.
        Exception: For any other browser or network related errors.

    Example:
        >>> import asyncio
        >>> data = asyncio.run(scrape_webpage("https://news.ycombinator.com"))
        >>> print(data["title"])
        >>> print(data["content"][:500])
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )

            page = await context.new_page()
            await page.goto(url, wait_until=wait_for, timeout=timeout)

            # Extract both title and body text in a single evaluate call
            # to avoid multiple round trips to the browser
            result = await page.evaluate("""
                () => {
                    const title = document.title ?? "";

                    // Remove non-visible / non-content elements
                    const tagsToRemove = ['script', 'style', 'noscript', 'svg', 'img'];
                    tagsToRemove.forEach(tag => {
                        document.querySelectorAll(tag).forEach(el => el.remove());
                    });

                    const content = document.body.innerText ?? "";

                    return { title, content };
                }
            """)

            # Normalize excessive whitespace and blank lines
            lines = [line.strip() for line in result["content"].splitlines()]
            cleaned_content = "\n".join(line for line in lines if line)

            return PageData(
                url=url,
                title=result["title"].strip(),
                content=cleaned_content,
            )

        except PlaywrightTimeoutError:
            raise PlaywrightTimeoutError(
                f"Page '{url}' did not finish loading within {timeout}ms. "
                "Try increasing the timeout or using a different wait_for strategy."
            )
        finally:
            await browser.close()


def scrape(url: str, wait_for: str = "networkidle", timeout: int = 30000) -> PageData:
    """
    Synchronous wrapper around :func:`scrape_webpage`.

    Useful when you are not inside an async context and want a simple
    one-liner call.

    Args:
        url (str): The full URL of the webpage to scrape.
        wait_for (str): Load condition — see :func:`scrape_webpage` for options.
        timeout (int): Timeout in milliseconds. Defaults to 30000.

    Returns:
        PageData: A TypedDict containing ``url``, ``title``, and ``content``.
                  See :func:`scrape_webpage` for full field descriptions.

    Example:
        >>> from scraper import scrape
        >>> data = scrape("https://news.ycombinator.com")
        >>> print(data["title"])
        >>> print(data["content"][:300])
    """
    return asyncio.run(scrape_webpage(url, wait_for=wait_for, timeout=timeout))


async def get_page_links(
    url: str,
    wait_for: str = "networkidle",
    timeout: int = 30000,
    include_external: bool = True,
) -> PageLinks:
    """
    Extract all hyperlinks from a fully rendered webpage using Playwright.

    Navigates to the page with a real browser so JavaScript-rendered links
    (e.g. those injected by React/Vue routers) are captured. Relative URLs
    are resolved to absolute form using the page's own origin, and blank,
    fragment-only (``#``), and ``javascript:`` hrefs are filtered out.

    Args:
        url (str): The full URL of the webpage to scrape
                   (e.g. "https://example.com").
        wait_for (str): The condition to wait for before extracting links.
                        Options:
                          - "networkidle"      → waits until network has been idle
                                                 for 500ms (best for SPAs). [default]
                          - "domcontentloaded" → waits for the HTML to be parsed.
                          - "load"             → waits for the load event.
                          - "commit"           → waits until the response starts arriving.
        timeout (int): Maximum time in milliseconds to wait for the page to load.
                       Defaults to 30000 (30 seconds).
        include_external (bool): When ``True`` (default), links pointing to other
                                 domains are included. Set to ``False`` to return
                                 only links whose resolved href shares the same
                                 origin as ``url``.

    Returns:
        PageLinks: A TypedDict containing:
            - ``url``   (str): The URL that was scraped.
            - ``links`` (list[Link]): Deduplicated list of links, each with:
                - ``href`` (str): Absolute URL of the link.
                - ``text`` (str): Visible anchor text, whitespace-normalised.

    Raises:
        PlaywrightTimeoutError: If the page does not load within the timeout period.
        Exception: For any other browser or network related errors.

    Example:
        >>> import asyncio
        >>> data = asyncio.run(get_page_links("https://news.ycombinator.com"))
        >>> for link in data["links"][:5]:
        ...     print(link["href"], "|", link["text"])
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )

            page = await context.new_page()
            await page.goto(url, wait_until=wait_for, timeout=timeout)

            raw_links: list[dict[str, str]] = await page.evaluate("""
                () => {
                    const origin = window.location.origin;
                    const seen = new Set();
                    const results = [];

                    document.querySelectorAll("a[href]").forEach(el => {
                        const raw = el.getAttribute("href").trim();

                        // Skip blank, fragment-only, and javascript: hrefs
                        if (!raw || raw === "#" || raw.startsWith("javascript:")) return;

                        // Resolve relative URLs to absolute
                        let href;
                        try {
                            href = new URL(raw, window.location.href).href;
                        } catch {
                            return;  // malformed href — skip
                        }

                        // Deduplicate by resolved href
                        if (seen.has(href)) return;
                        seen.add(href);

                        const text = (el.innerText || el.textContent || "").trim()
                            .replace(/\\s+/g, " ");

                        results.push({ href, text });
                    });

                    return results;
                }
            """)

            if not include_external:
                from urllib.parse import urlparse
                base_origin = urlparse(url).netloc
                raw_links = [
                    link for link in raw_links
                    if urlparse(link["href"]).netloc == base_origin
                ]

            return PageLinks(url=url, links=raw_links)

        except PlaywrightTimeoutError:
            raise PlaywrightTimeoutError(
                f"Page '{url}' did not finish loading within {timeout}ms. "
                "Try increasing the timeout or using a different wait_for strategy."
            )
        finally:
            await browser.close()


def get_links(
    url: str,
    wait_for: str = "networkidle",
    timeout: int = 30000,
    include_external: bool = True,
) -> PageLinks:
    """
    Synchronous wrapper around :func:`get_page_links`.

    Useful when you are not inside an async context and want a simple
    one-liner call.

    Args:
        url (str): The full URL of the webpage to scrape.
        wait_for (str): Load condition — see :func:`get_page_links` for options.
        timeout (int): Timeout in milliseconds. Defaults to 30000.
        include_external (bool): Include links to other domains. Defaults to ``True``.

    Returns:
        PageLinks: A TypedDict containing ``url`` and ``links``.
                   See :func:`get_page_links` for full field descriptions.

    Example:
        >>> from playwright_scraper import get_links
        >>> data = get_links("https://news.ycombinator.com", include_external=False)
        >>> for link in data["links"][:10]:
        ...     print(link["href"], "|", link["text"])
    """
    return asyncio.run(
        get_page_links(url, wait_for=wait_for, timeout=timeout, include_external=include_external)
    )


if __name__ == "__main__":
    # url = "https://news.ycombinator.com"
    url = "https://openai.com/index/introducing-openai-frontier/"
    # url = "https://openai.com"
    print(f"Scraping: {url}\n{'=' * 50}")
    data = scrape(url, wait_for="domcontentloaded", timeout=120000)  # Increase timeout for slower pages

    print(f"Title   : {data['title']}")
    print(f"URL     : {data['url']}")
    print(f"{'=' * 50}")
    print(data["content"][:5000])
    print(f"\n{'=' * 50}")
    print(f"Total characters scraped: {len(data['content'])}")

    # all links
    print("All Links")
    # all_links = get_links("https://openai.com", wait_for="domcontentloaded", timeout=120000)
    all_links = get_links("https://huggingface.co", wait_for="domcontentloaded", timeout=120000) 
    for link in all_links["links"]:
        print(link["href"], "|", link["text"])
    print(f"\n{'=' * 50}")

    # internal links only
    print("Internal Links only")
    # internal_links = get_links("https://openai.com", wait_for="domcontentloaded", timeout=120000, include_external=False)
    internal_links = get_links("https://huggingface.co", wait_for="domcontentloaded", timeout=120000, include_external=False)

    for link in internal_links["links"]:
        print(link["href"], "|", link["text"])
