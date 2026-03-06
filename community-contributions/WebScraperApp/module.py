import urllib.request
import urllib.parse
import urllib.error
import html.parser
import re
from datetime import datetime
import time
import ssl
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from functools import partial

class HTMLParser(html.parser.HTMLParser):
    """Custom HTML parser to extract title, links, and text content"""
    
    def __init__(self):
        super().__init__()
        self.title = ""
        self.links = []
        self.text_content = []
        self.in_title = False
        self.in_body = False
        self.current_tag = ""
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag.lower()
        
        if tag.lower() == 'title':
            self.in_title = True
        elif tag.lower() == 'body':
            self.in_body = True
        elif tag.lower() == 'a':
            # Extract href attribute
            for attr, value in attrs:
                if attr.lower() == 'href' and value:
                    self.links.append(value)
                    
    def handle_endtag(self, tag):
        if tag.lower() == 'title':
            self.in_title = False
        elif tag.lower() == 'body':
            self.in_body = False
            
    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif self.in_body and self.current_tag in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'li']:
            # Clean the text data
            cleaned_data = re.sub(r'\s+', ' ', data.strip())
            if cleaned_data:
                self.text_content.append(cleaned_data)
                
    def get_text(self):
        """Return all extracted text content as a single string"""
        return ' '.join(self.text_content)
        
    def get_clean_text(self, max_length=500):
        """Return cleaned text content with length limit"""
        text = self.get_text()
        # Remove extra whitespace and limit length
        text = re.sub(r'\s+', ' ', text.strip())
        if len(text) > max_length:
            text = text[:max_length] + "..."
        return text

class Website:
    """Class to store website data"""
    
    def __init__(self, title, url, content, depth, links=None, load_time=None):
        self.title = title or "No Title"
        self.url = url
        self.content = content
        self.depth = depth
        self.links = links or []
        self.load_time = load_time
        self.timestamp = datetime.now()
        
    def get_word_count(self):
        """Get word count from content"""
        if not self.content:
            return 0
        # Extract text content and count words
        text_content = re.sub(r'<[^>]+>', '', self.content)
        words = text_content.split()
        return len(words)
        
    def get_domain(self):
        """Extract domain from URL"""
        try:
            parsed = urlparse(self.url)
            return parsed.netloc
        except:
            return ""
            
    def get_normalized_domain(self):
        """Get domain without www prefix for consistent filtering"""
        domain = self.get_domain()
        if domain.startswith('www.'):
            return domain[4:]
        return domain
        
    def search_content(self, query):
        """Search for query in content"""
        if not self.content or not query:
            return False
        return query.lower() in self.content.lower()
        
    def get_text_preview(self, max_length=200):
        """Get a text preview of the content"""
        if not self.content:
            return "No content available"
        
        # Extract text content
        text_content = re.sub(r'<[^>]+>', '', self.content)
        text_content = re.sub(r'\s+', ' ', text_content.strip())
        
        if len(text_content) > max_length:
            return text_content[:max_length] + "..."
        return text_content

class WebScraper:
    """Web scraper with multithreading support and robust duplicate detection"""
    
    def __init__(self):
        self.websites = []
        self.visited_urls = set()
        self.visited_domains = set()  # Track visited domains
        self.start_domain = None      # Store the starting domain
        self.lock = threading.Lock()
        self.max_workers = 10  # Number of concurrent threads
        # Removed all page limits - unlimited crawling
        self.domain_page_counts = {}  # Track page count per domain (for statistics only)
        self._stop_requested = False  # Flag to stop scraping
        
    def normalize_url(self, url):
        """Normalize URL to handle www prefixes and remove fragments"""
        if not url:
            return url
            
        # Remove fragments (#) to prevent duplicate content
        if '#' in url:
            url = url.split('#')[0]
            
        # Remove trailing slashes for consistency
        url = url.rstrip('/')
            
        # Remove www prefix for consistent domain handling
        if url.startswith('https://www.'):
            return url.replace('https://www.', 'https://', 1)
        elif url.startswith('http://www.'):
            return url.replace('http://www.', 'http://', 1)
        return url
        
    def get_domain_from_url(self, url):
        """Extract and normalize domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain.startswith('www.'):
                return domain[4:]
            return domain
        except:
            return ""
            
    def should_skip_url(self, url, current_depth):
        """Check if URL should be skipped based on various criteria"""
        normalized_url = self.normalize_url(url)
        
        # Skip if already visited
        if normalized_url in self.visited_urls:
            return True, "Already visited"
            
        # Skip if not a valid HTTP/HTTPS URL
        if not normalized_url.startswith(('http://', 'https://')):
            return True, "Not HTTP/HTTPS URL"
            
        # Get domain
        domain = self.get_domain_from_url(normalized_url)
        if not domain:
            return True, "Invalid domain"
            
        # Removed all domain page limits - unlimited crawling
        # Removed external domain depth limits - crawl as deep as needed
            
        return False, "OK"
    
    def scrape_url(self, url, depth):
        """Scrape a single URL with error handling and rate limiting"""
        try:
            # Check if stop was requested
            if self._stop_requested:
                return None
                
            # Check if URL should be skipped
            should_skip, reason = self.should_skip_url(url, depth)
            if should_skip:
                print(f"Skipping {url}: {reason}")
                return None
            
            # Normalize URL
            normalized_url = self.normalize_url(url)
            
            # Mark as visited and update domain count (for statistics only)
            with self.lock:
                self.visited_urls.add(normalized_url)
                domain = self.get_domain_from_url(normalized_url)
                if domain:
                    self.domain_page_counts[domain] = self.domain_page_counts.get(domain, 0) + 1
            
            # Add small delay to prevent overwhelming servers
            time.sleep(0.1)
            
            start_time = time.time()
            
            # Create request with headers
            req = urllib.request.Request(
                normalized_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            # Fetch the page with timeout
            with urllib.request.urlopen(req, timeout=15) as response:
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                    print(f"Skipping {url}: Not HTML content ({content_type})")
                    return None
                
                html_content = response.read().decode('utf-8', errors='ignore')
                
            load_time = time.time() - start_time
            
            # Skip if content is too small (likely error page)
            if len(html_content) < 100:
                print(f"Skipping {url}: Content too small ({len(html_content)} chars)")
                return None
            
            # Parse HTML
            parser = HTMLParser()
            parser.feed(html_content)
            
            # Extract links and normalize them with duplicate detection
            links = []
            base_url = normalized_url
            seen_links = set()  # Track links within this page to avoid duplicates
            
            for link in parser.links:
                try:
                    absolute_url = urljoin(base_url, link)
                    normalized_link = self.normalize_url(absolute_url)
                    
                    # Skip if already seen in this page or should be skipped
                    if normalized_link in seen_links:
                        continue
                    seen_links.add(normalized_link)
                    
                    should_skip, reason = self.should_skip_url(normalized_link, depth + 1)
                    if should_skip:
                        continue
                    
                    # Only include http/https links and filter out common non-content URLs
                    if (normalized_link.startswith(('http://', 'https://')) and 
                        not any(skip in normalized_link.lower() for skip in [
                            'mailto:', 'tel:', 'javascript:', 'data:', 'file:',
                            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar',
                            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
                            '.css', '.js', '.xml', '.json', '.txt', '.log'
                        ])):
                        links.append(normalized_link)
                except:
                    continue
            
            # Create Website object
            website = Website(
                title=parser.title,
                url=normalized_url,
                content=html_content,
                depth=depth,
                links=links,
                load_time=load_time
            )
            
            return website
            
        except urllib.error.HTTPError as e:
            print(f"HTTP Error scraping {url}: {e.code} - {e.reason}")
            return None
        except urllib.error.URLError as e:
            print(f"URL Error scraping {url}: {e.reason}")
            return None
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
    
    def crawl_website(self, start_url, max_depth=3, progress_callback=None):
        """Crawl website with multithreading support and no page limits"""
        if not start_url.startswith(('http://', 'https://')):
            start_url = 'https://' + start_url
            
        # Initialize tracking
        self.websites = []
        self.visited_urls = set()
        self.visited_domains = set()
        self.domain_page_counts = {}
        self.start_domain = self.get_domain_from_url(start_url)
        self._stop_requested = False  # Reset stop flag
        
        print(f"Starting crawl from: {start_url}")
        print(f"Starting domain: {self.start_domain}")
        print(f"Max depth: {max_depth}")
        print(f"Unlimited crawling - no page limits")
        
        # Start with the initial URL
        urls_to_scrape = [(start_url, 0)]
        max_depth_reached = 0
        consecutive_empty_levels = 0
        max_consecutive_empty = 3  # Stop if 3 consecutive levels have no new URLs
        total_pages_scraped = 0
        # Removed all page limits - unlimited crawling
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for current_depth in range(max_depth + 1):
                # Check if stop was requested
                if self._stop_requested:
                    print("Scraping stopped by user request")
                    break
                    
                if not urls_to_scrape:
                    print(f"Stopping at depth {current_depth}: No more URLs to scrape")
                    break
                
                # Check if we've reached too many consecutive empty levels
                if consecutive_empty_levels >= max_consecutive_empty:
                    print(f"Stopping at depth {current_depth}: {max_consecutive_empty} consecutive empty levels")
                    break
                
                # Removed absolute page limit check - unlimited pages
                
                print(f"Scraping depth {current_depth} with {len(urls_to_scrape)} URLs")
                
                # Submit all URLs at current depth for concurrent scraping
                future_to_url = {
                    executor.submit(self.scrape_url, url, depth): url 
                    for url, depth in urls_to_scrape
                }
                
                # Collect results and prepare next level
                urls_to_scrape = []
                level_results = 0
                
                for future in as_completed(future_to_url):
                    # Check if stop was requested
                    if self._stop_requested:
                        print("Stopping processing of current level")
                        break
                        
                    website = future.result()
                    if website:
                        with self.lock:
                            self.websites.append(website)
                        level_results += 1
                        total_pages_scraped += 1
                        
                        # Emit progress if callback provided
                        if progress_callback:
                            progress_callback(website)
                        
                        # Add links for next depth level (no limits)
                        if current_depth < max_depth:
                            for link in website.links:
                                # Removed URL limit per level - process all URLs
                                
                                should_skip, reason = self.should_skip_url(link, current_depth + 1)
                                if not should_skip:
                                    urls_to_scrape.append((link, current_depth + 1))
                
                # Check if stop was requested after processing level
                if self._stop_requested:
                    break
                
                # Update depth tracking
                if level_results > 0:
                    max_depth_reached = current_depth
                    consecutive_empty_levels = 0
                else:
                    consecutive_empty_levels += 1
                
                # Only stop if we've reached the actual max depth
                if current_depth >= max_depth:
                    print(f"Reached maximum depth: {max_depth}")
                    break
                
                # Print progress summary
                print(f"Depth {current_depth} completed: {level_results} pages, Total: {len(self.websites)}")
                if self.domain_page_counts:
                    print(f"Domain breakdown: {dict(self.domain_page_counts)}")
        
        print(f"Crawling completed. Max depth reached: {max_depth_reached}, Total pages: {len(self.websites)}")
        print(f"Visited URLs: {len(self.visited_urls)}")
        print(f"Domain breakdown: {dict(self.domain_page_counts)}")
        return self.websites
    
    def reset(self):
        """Reset the scraper state for a new crawl"""
        self.websites = []
        self.visited_urls = set()
        self.visited_domains = set()
        self.domain_page_counts = {}
        self.start_domain = None
        self._stop_requested = False  # Reset stop flag
        
    def get_statistics(self):
        """Get scraping statistics with enhanced tracking information"""
        if not self.websites:
            return {
                'total_pages': 0,
                'total_links': 0,
                'total_words': 0,
                'avg_load_time': 0,
                'max_depth_reached': 0,
                'domains': {},
                'visited_urls_count': 0,
                'domain_page_counts': {},
                'start_domain': self.start_domain
            }
        
        total_pages = len(self.websites)
        total_links = sum(len(w.links) for w in self.websites)
        total_words = sum(w.get_word_count() for w in self.websites)
        
        load_times = [w.load_time for w in self.websites if w.load_time]
        avg_load_time = sum(load_times) / len(load_times) if load_times else 0
        
        max_depth_reached = max(w.depth for w in self.websites)
        
        # Count domains
        domains = {}
        for website in self.websites:
            domain = website.get_normalized_domain()
            domains[domain] = domains.get(domain, 0) + 1
        
        return {
            'total_pages': total_pages,
            'total_links': total_links,
            'total_words': total_words,
            'avg_load_time': avg_load_time,
            'max_depth_reached': max_depth_reached,
            'domains': domains,
            'visited_urls_count': len(self.visited_urls),
            'domain_page_counts': dict(self.domain_page_counts),
            'start_domain': self.start_domain
        }
    
    def filter_by_domain(self, domain):
        """Filter websites by domain"""
        normalized_domain = self.normalize_url(domain)
        return [w for w in self.websites if w.get_normalized_domain() == normalized_domain]
    
    def search_websites(self, query):
        """Search websites by query"""
        return [w for w in self.websites if w.search_content(query)]
    
    def stop_scraping(self):
        """Request graceful stop of the scraping process"""
        self._stop_requested = True