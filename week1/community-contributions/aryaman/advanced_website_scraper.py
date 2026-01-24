"""
Advanced Website Scraper

An improved web scraping class that can handle both static and JavaScript-rendered pages.
Uses Playwright for JavaScript-heavy sites and BeautifulSoup for static sites.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import Optional, List, Dict, Any

# Try to import OpenAI for Ollama integration
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to import Playwright, but make it optional
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Standard headers to fetch a website
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


class AdvancedWebsite:
    """
    An advanced web scraping class that can handle both static and JavaScript-rendered pages.
    
    Features:
    - Automatic detection of JavaScript-rendered content
    - Fallback to BeautifulSoup for static sites (faster)
    - Enhanced error handling with retry logic
    - Better text extraction and cleaning
    - Improved link extraction and validation
    - Metadata extraction (description, keywords, Open Graph tags)
    
    Usage:
        # Automatic mode (tries Playwright first, falls back to requests)
        website = AdvancedWebsite("https://openai.com")
        
        # Force JavaScript rendering
        website = AdvancedWebsite("https://openai.com", use_js=True)
        
        # Static site (faster)
        website = AdvancedWebsite("https://example.com", use_js=False)
    """
    
    def __init__(
        self,
        url: str,
        use_js: bool = False,
        timeout: int = 30,
        wait_for_selector: Optional[str] = None,
        retries: int = 2,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the AdvancedWebsite scraper.
        
        Args:
            url: The URL to scrape
            use_js: If True, use Playwright for JavaScript rendering. If False, try requests first.
            timeout: Timeout in seconds for page loading
            wait_for_selector: CSS selector to wait for before extracting content
            retries: Number of retry attempts for failed requests
            headers: Custom headers to use for requests
        """
        self.url = url
        self.use_js = use_js
        self.timeout = timeout
        self.wait_for_selector = wait_for_selector
        self.retries = retries
        self.headers = headers or DEFAULT_HEADERS.copy()
        
        self.html = ""
        self.title = ""
        self.text = ""
        self.links = []
        self.metadata = {}
        self.soup = None
        self._fetch_method = None
        
        # Fetch and parse the content
        self._fetch_content()
        if self.html:
            self._parse_content()
    
    def _fetch_content(self):
        """Fetch the HTML content using the appropriate method."""
        if self.use_js:
            if PLAYWRIGHT_AVAILABLE:
                self._fetch_with_playwright()
            else:
                print("Warning: Playwright not available. Falling back to requests.")
                self._fetch_with_requests()
        else:
            # Try requests first (faster for static sites)
            success = self._fetch_with_requests()
            # If requests fails or returns minimal content, try Playwright
            if not success and PLAYWRIGHT_AVAILABLE:
                print("Requests method didn't work well. Trying Playwright...")
                self._fetch_with_playwright()
    
    def _fetch_with_requests(self) -> bool:
        """
        Fetch content using requests library (faster for static sites).
        
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(self.retries + 1):
            try:
                response = requests.get(
                    self.url,
                    headers=self.headers,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                response.raise_for_status()
                self.html = response.text
                self._fetch_method = "requests"
                return True
            except requests.exceptions.RequestException as e:
                if attempt < self.retries:
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(1)
                else:
                    print(f"Failed to fetch {self.url} after {self.retries + 1} attempts: {e}")
                    self.html = ""
                    return False
        return False
    
    def _fetch_with_playwright(self) -> bool:
        """
        Fetch content using Playwright (handles JavaScript-rendered pages).
        
        Returns:
            True if successful, False otherwise
        """
        if not PLAYWRIGHT_AVAILABLE:
            print("Error: Playwright is not installed. Install it with: pip install playwright && playwright install")
            return False
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=self.headers.get("User-Agent", DEFAULT_HEADERS["User-Agent"])
                )
                page = context.new_page()
                
                # Navigate to the page
                page.goto(self.url, wait_until="networkidle", timeout=self.timeout * 1000)
                
                # Wait for specific selector if provided
                if self.wait_for_selector:
                    try:
                        page.wait_for_selector(self.wait_for_selector, timeout=10000)
                    except PlaywrightTimeoutError:
                        print(f"Warning: Selector '{self.wait_for_selector}' not found, continuing anyway...")
                
                # Get the rendered HTML
                self.html = page.content()
                self._fetch_method = "playwright"
                
                browser.close()
                return True
                
        except Exception as e:
            print(f"Error fetching with Playwright: {e}")
            self.html = ""
            return False
    
    def _parse_content(self):
        """Parse the HTML content using BeautifulSoup."""
        if not self.html:
            return
        
        try:
            self.soup = BeautifulSoup(self.html, 'html.parser')
            self._extract_title()
            self._extract_text()
            self._extract_links()
            self._extract_metadata()
        except Exception as e:
            print(f"Error parsing content: {e}")
    
    def _extract_title(self):
        """Extract the page title."""
        if self.soup and self.soup.title:
            self.title = self.soup.title.string.strip() if self.soup.title.string else "No title found"
        else:
            # Try Open Graph title
            og_title = self.soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                self.title = og_title["content"]
            else:
                self.title = "No title found"
    
    def _extract_text(self):
        """Extract and clean text content from the page."""
        if not self.soup or not self.soup.body:
            self.text = ""
            return
        
        # Create a copy to avoid modifying the original
        body = self.soup.body
        
        # Remove irrelevant elements
        irrelevant_tags = ["script", "style", "img", "input", "nav", "header", "footer", 
                          "aside", "noscript", "iframe", "svg", "canvas"]
        for tag in irrelevant_tags:
            for element in body.find_all(tag):
                element.decompose()
        
        # Remove elements with common ad/analytics classes
        for element in body.find_all(class_=lambda x: x and any(
            keyword in x.lower() for keyword in ['ad', 'advertisement', 'ads', 'analytics', 
                                                 'cookie', 'popup', 'modal', 'overlay']
        )):
            element.decompose()
        
        # Extract text with better formatting
        self.text = body.get_text(separator="\n", strip=True)
        
        # Clean up excessive whitespace
        lines = [line.strip() for line in self.text.split("\n") if line.strip()]
        self.text = "\n".join(lines)
    
    def _extract_links(self):
        """Extract and validate links from the page."""
        if not self.soup:
            self.links = []
            return
        
        links = []
        base_url = self.url
        
        for link in self.soup.find_all("a", href=True):
            href = link.get("href")
            if not href:
                continue
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Validate URL
            parsed = urlparse(absolute_url)
            if parsed.scheme in ("http", "https"):
                links.append(absolute_url)
        
        # Remove duplicates while preserving order
        seen = set()
        self.links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                self.links.append(link)
    
    def _extract_metadata(self):
        """Extract metadata from the page (description, keywords, Open Graph tags, etc.)."""
        if not self.soup:
            self.metadata = {}
            return
        
        metadata = {}
        
        # Standard meta tags
        meta_description = self.soup.find("meta", attrs={"name": "description"})
        if meta_description and meta_description.get("content"):
            metadata["description"] = meta_description["content"]
        
        meta_keywords = self.soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords and meta_keywords.get("content"):
            metadata["keywords"] = meta_keywords["content"]
        
        # Open Graph tags
        og_tags = {}
        for og_tag in self.soup.find_all("meta", property=lambda x: x and x.startswith("og:")):
            prop = og_tag.get("property", "").replace("og:", "")
            content = og_tag.get("content", "")
            if prop and content:
                og_tags[prop] = content
        
        if og_tags:
            metadata["open_graph"] = og_tags
        
        # Twitter Card tags
        twitter_tags = {}
        for twitter_tag in self.soup.find_all("meta", attrs={"name": lambda x: x and x.startswith("twitter:")}):
            name = twitter_tag.get("name", "").replace("twitter:", "")
            content = twitter_tag.get("content", "")
            if name and content:
                twitter_tags[name] = content
        
        if twitter_tags:
            metadata["twitter_card"] = twitter_tags
        
        # Author
        author = self.soup.find("meta", attrs={"name": "author"})
        if author and author.get("content"):
            metadata["author"] = author["content"]
        
        self.metadata = metadata
    
    def get_contents(self, max_length: Optional[int] = None) -> str:
        """
        Get formatted contents of the webpage.
        
        Args:
            max_length: Maximum length of the returned text (None for no limit)
        
        Returns:
            Formatted string with title and content
        """
        text = self.text
        if max_length and len(text) > max_length:
            text = text[:max_length] + "..."
        
        return f"Webpage Title:\n{self.title}\n\nWebpage Contents:\n{text}\n"
    
    def get_links(self) -> List[str]:
        """
        Get all links found on the page.
        
        Returns:
            List of absolute URLs
        """
        return self.links.copy()
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata extracted from the page.
        
        Returns:
            Dictionary containing metadata
        """
        return self.metadata.copy()
    
    def get_fetch_method(self) -> str:
        """
        Get the method used to fetch the page.
        
        Returns:
            "playwright", "requests", or "unknown"
        """
        return self._fetch_method or "unknown"
    
    def summarize_with_ollama(
        self,
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
        temperature: float = 0,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Summarize the website content using Ollama via OpenAI-compatible API.
        
        Args:
            model: The Ollama model to use (e.g., "llama3.1", "llama3.2")
            base_url: The base URL for Ollama API (default: http://localhost:11434/v1)
            api_key: API key for Ollama (default: "ollama")
            temperature: Temperature for generation (0 for deterministic, default: 0)
            max_tokens: Maximum tokens in response (None for no limit)
            system_prompt: Custom system prompt (None uses default)
        
        Returns:
            Summary of the website content
        
        Raises:
            ImportError: If OpenAI library is not installed
            Exception: If summarization fails
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI library is required for summarization. "
                "Install it with: pip install openai"
            )
        
        if not self.text:
            return "No content available to summarize."
        
        # Prepare the content to summarize
        content_to_summarize = f"Title: {self.title}\n\nContent:\n{self.text}"
        
        # Limit content length if too long (to avoid token limits)
        max_content_length = 8000  # Reasonable limit for most models
        if len(content_to_summarize) > max_content_length:
            content_to_summarize = content_to_summarize[:max_content_length] + "..."
        
        # Default system prompt
        if system_prompt is None:
            system_prompt = (
                "You are a helpful assistant that summarizes website content. "
                "Provide a clear, concise summary of the key points and main information."
            )
        
        # Create OpenAI client pointing to Ollama
        client = OpenAI(base_url=base_url, api_key=api_key)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please summarize the following website content:\n\n{content_to_summarize}"}
        ]
        
        try:
            # Create completion parameters
            completion_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            
            if max_tokens:
                completion_params["max_tokens"] = max_tokens
            
            # Call Ollama via OpenAI-compatible API
            response = client.chat.completions.create(**completion_params)
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(
                f"Failed to summarize website: {e}\n"
                f"Make sure Ollama is running: ollama serve\n"
                f"And the model is available: ollama pull {model}"
            )
    
    def summarize(
        self,
        model: str = "llama3.1",
        temperature: float = 0,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Convenience method to summarize the website using default Ollama settings.
        
        Args:
            model: The Ollama model to use (default: "llama3.1")
            temperature: Temperature for generation (default: 0)
            max_tokens: Maximum tokens in response (None for no limit)
        
        Returns:
            Summary of the website content
        """
        return self.summarize_with_ollama(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

