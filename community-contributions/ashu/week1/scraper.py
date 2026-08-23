from bs4 import BeautifulSoup
import requests

# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


class WebsiteScraper:
    
    """Represents a web page and provides utilities for extracting content and links."""

    def __init__(self, url:str):
        """
        Fetch and parse the web page.

        Args:
            url: URL of the page to retrieve.

        Raises:
            requests.HTTPError: If the request fails.
        """
        self.url = url
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()

        self.soup = BeautifulSoup(response.text, "html.parser")

    @property
    def title(self) -> str:
        """
        Return the page title.

        Returns:
            The contents of the <title> tag, or a fallback message
            if no title is present.
        """
        return self.soup.title.string.strip() if self.soup.title else "NO TITLE FOUND"

    def get_content(self, limit: int = 2000) -> str:
        """
        Extract readable text from the page body.

        Removes non-content elements such as scripts, styles,
        images, and form inputs before extracting text.

        Args:
            limit: Maximum number of characters to return.

        Returns:
            A string containing the page title followed by the
            extracted body text.
        """
        if not self.soup.body:
            return self.title

        for tag in self.soup(["script", "style", "img", "input"]):
            tag.decompose()

        text = self.soup.body.get_text(separator="\n", strip=True)
        
        return f"{self.title}\n\n{text[:limit]}"

    def get_links(self) -> list[str]:
        """
        Extract all hyperlinks from the page.

        Returns:
            A list of href values from anchor tags.
        """
        return [link.get("href") for link in self.soup.find_all("a", href=True) if link.get("href")]