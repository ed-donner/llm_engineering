from ipaddress import ip_address, IPv4Address, IPv6Address
from urllib.parse import ParseResult, urlparse
from bs4 import BeautifulSoup, Tag
from requests import get, RequestException, Session

class Extractor:
    """
    Extracts and processes content from HTML response text using BeautifulSoup.
    """
    __soup: BeautifulSoup

    __extracted_title: str = ""
    @property
    def extracted_title(self) -> str:
        """
        Returns the extracted title from the HTML content.
        """
        if not self.__extracted_title:
            self.__extracted_title = self.get_title()
        return self.__extracted_title

    __extracted_text: str = ""
    @property
    def extracted_text(self) -> str:
        """
        Returns the extracted main text content from the HTML, excluding irrelevant tags.
        """
        if not self.__extracted_text:
            self.__extracted_text = self.get_text()
        return self.__extracted_text

    __extracted_links_on_page: list[str] | None = None
    @property
    def extracted_links_on_page(self) -> list[str]:
        """
        Return all href values found on the page.

        Notes:
            - Only anchor tags with an href are included.
            - Values are returned as-is (may be relative or absolute).
        """
        if self.__extracted_links_on_page is None:
            self.__extracted_links_on_page = [str(a.get("href")) for a in self._soup.find_all('a', href=True) if isinstance(a, Tag)]
        return self.__extracted_links_on_page

    @property
    def _soup(self) -> BeautifulSoup:
        """
        Returns the BeautifulSoup object for the HTML content.
        """
        return self.__soup
    
    def __init__(self, response_text_content: str) -> None:
        """
        Initializes the Extractor with HTML response text.

        Parameters:
            response_text_content (str): The HTML response text to be processed.
        """
        self.__soup = BeautifulSoup(response_text_content, "html.parser")
        self.__extracted_links_on_page = None

    def get_title(self) -> str:
        """
        Extracts the title from the HTML content.
        """
        return self._soup.title.get_text() if self._soup.title is not None else "No title"

    def get_text(self) -> str:
        """
        Extracts and cleans the main text content from the HTML, removing irrelevant tags.
        """
        for irrelevant in self._soup.find_all(["script", "style", "img", "figure", "video", "audio", "button", "svg", "canvas", "input", "form", "meta"]):
            irrelevant.decompose()
        raw_text: str = self._soup.get_text(separator="\n")
        cleaned_text: str = " ".join(raw_text.split())
        return cleaned_text if cleaned_text else "No content"

class Website:
    """
    A class to represent a website.
    """

    __DEFAULT_ALLOWED_DOMAINS: list[str] = [".com", ".org", ".net"]

    __title: str = ""
    __website_url: str = ""
    __text: str = ""
    __allowed_domains: list[str] = []
    __links_on_page: list[str] | None = None

    @property
    def title(self) -> str:
        """
        Returns the title of the website.
        """
        return self.__title

    @property
    def text(self) -> str:
        """
        Returns the main text content of the website.
        """
        return self.__text

    @property
    def website_url(self) -> str:
        """
        Returns the URL of the website.
        """
        return self.__website_url

    @property
    def links_on_page(self) -> list[str] | None:
        """
        Returns the list of links extracted from the website.
        """
        return self.__links_on_page

    @property
    def _allowed_domains(self) -> list[str]:
        """
        Returns the list of allowed domain suffixes.
        """
        return self.__allowed_domains

    @_allowed_domains.setter
    def _allowed_domains(self, value: list[str] | str) -> None:
        """
        Sets the list of allowed domain suffixes.
        Filters out empty strings and ensures each suffix starts with a dot.
        """
        if isinstance(value, str):
            value = [
                item.strip() if item.strip().startswith(".") else f".{item.strip()}"
                for item in value.split(",")
                if item.strip()
            ]
        else:
            value = [
                item if item.startswith(".") else f".{item}"
                for item in value
                if item
            ]
        self.__allowed_domains = value

    def _set_website_url(self, value: str) -> None:
        """
        Protected: set the website URL after validating and fetch website data.
        Use this from inside the class to initialize or change the URL.
        """
        if not value:
            raise ValueError("Website URL must be provided")

        parsed_url: ParseResult = urlparse(value)

        self._validate(parsed_url)

        self.__website_url = value
        self.__fetch_website_data()

    @property
    def fetch_failed(self) -> bool:
        """
        Returns whether the website data fetch failed.
        """
        return self.__fetch_failed

    def _validate(self, parsed_url: ParseResult) -> None:
        """
        Validate the parsed URL.

        Parameters:
            parsed_url: The parsed URL to validate.

        Raises:
            ValueError: If the URL is missing parts, uses an invalid scheme,
                        points to a local/private address, or is not in allowed domains.
        """
        if not parsed_url.netloc or parsed_url.scheme not in ("http", "https"):
            raise ValueError("Website URL must be a valid URL")

        if not parsed_url.hostname:
            raise ValueError("Website URL must contain a valid hostname")

        if self.__is_local_address(parsed_url.hostname):
            raise ValueError("Website URL must not be a local address")

        if not self.__is_allowed_domain(parsed_url.hostname):
            raise ValueError("Website URL must be an allowed domain")

    def __is_local_address(self, hostname: str) -> bool:
        """
        Check if the given hostname is a local address.

        Parameters:
            hostname (str): The hostname to check.

        Returns:
            bool: True if the hostname is a local address, False otherwise.
        """
        if hostname in ("localhost", "127.0.0.1", "::1"):
            return True

        try:
            ip: IPv4Address | IPv6Address = ip_address(hostname)
            if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_reserved:
                return True
        except ValueError:
            return False

        return False

    def __is_allowed_domain(self, hostname: str) -> bool:
        """
        Check if the given hostname is an allowed domain.

        Parameters:
            hostname (str): The hostname to check.

        Returns:
            bool: True if the hostname is an allowed domain, False otherwise.
        """
        allowed_domains = [".com", ".org", ".net", ".io"]
        return any(hostname.endswith(domain) for domain in allowed_domains)

    def __fetch_website_data(self) -> None:
        """
        Fetch website content and populate title, text, and links.

        Side effects:
            - Sets internal state: __title, __text, __links_on_page, __fetch_failed.
            - Performs an HTTP GET with a browser-like User-Agent.
        """
        try:
            get_fn = self.__session.get if self.__session else get
            response = get_fn(
                self.website_url,
                timeout=10,
                verify=True,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}
            )
        except RequestException as e:
            self.__title = "Error"
            self.__text = str(e)
            self.__fetch_failed = True
            return
        
        if response.ok:
            extractor: Extractor = Extractor(response.text)
            self.__title = extractor.extracted_title
            self.__text = extractor.extracted_text
            self.__links_on_page = extractor.extracted_links_on_page
        else:
            if response.status_code == 404:
                self.__title = "Not Found"
                self.__text = "The requested page was not found (404)."
            else:
                self.__title = "Error"
                self.__text = f"Error: {response.status_code} - {response.reason}"
            self.__fetch_failed = True

    def __init__(self, website_url: str, allowed_domains: list[str] | str | None = None, session: Session | None = None) -> None:
        """
        Initializes the Website object and fetches its data.

        Parameters:
            website_url (str): The URL of the website to fetch.
            allowed_domains (list[str] | str, optional): A list of allowed domain suffixes.
                If a string is provided, it should be a comma-separated list of domain suffixes (e.g., ".com,.org,.net").
            session (requests.Session | None, optional): Reused HTTP session for connection pooling.
        """
        self.__fetch_failed: bool = False
        self.__session: Session | None = session
        if allowed_domains is None:
            self._allowed_domains = self.__DEFAULT_ALLOWED_DOMAINS.copy()
        else:
            self._allowed_domains = allowed_domains
        # Use protected setter internally so the public API exposes only the getter.
        self._set_website_url(website_url)

    def __str__(self) -> str:
        """
        Returns a string representation of the Website object.
        """
        return f"Website(title={self.title}, url={self.website_url})"