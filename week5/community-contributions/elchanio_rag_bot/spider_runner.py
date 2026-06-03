import scrapy
import os
from urllib.parse import urljoin, urlparse
from scrapy.crawler import CrawlerProcess

class IRWebSpider(scrapy.Spider):
    name= 'ir_web_spider'
    custom_settings = {
        'LOG_LEVEL': 'INFO',  # DEBUG, INFO, WARNING, ERROR
        'DOWNLOAD_DELAY': 1,   # Be nice to the server
        'ROBOTSTXT_OBEY': True,
    }
    num_pages = 10 # how many links to follow per page (Excluding documents)

    def __init__(self, start_urls=None, allowed_domains=None, *args, **kwargs):
        super(IRWebSpider, self).__init__(*args, **kwargs)
    
        # Handle start_urls
        if start_urls:
            if isinstance(start_urls, str):
                self.start_urls = [start_urls]
            else:
                self.start_urls = list(start_urls)
        else:
            self.start_urls = []
        
        # Handle allowed_domains
        if allowed_domains:
            if isinstance(allowed_domains, str):
                self.allowed_domains = [allowed_domains]
            else:
                self.allowed_domains = list(allowed_domains)
        else:
            # Auto-extract domains from start_urls if not provided
            self.allowed_domains = []
            for url in self.start_urls:
                domain = urlparse(url).netloc
                if domain and domain not in self.allowed_domains:
                    self.allowed_domains.append(domain)
        # Log initialization
        self.logger.info(f"Spider initialized with start_urls: {self.start_urls}")
        self.logger.info(f"Allowed domains: {self.allowed_domains}")
    
    def start_requests(self):
        urls = self.start_urls
        if not urls:
            raise ValueError("No URLs provided to scrape.")
        for url in urls:
            self.logger.info(f"Starting request to: {url}")
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        self.logger.info(f"Parsing response from: {response.url}")
        self.logger.info(f"Response status: {response.status}")
        # Save the page content
       
        # Extract document links with better selectors
        doc_selectors = [
            'a[href$=".pdf"]::attr(href)',
            'a[href$=".xlsx"]::attr(href)',
            'a[href$=".xls"]::attr(href)',
            'a[href$=".docx"]::attr(href)',
            'a[href$=".doc"]::attr(href)',
            'a[href$=".pptx"]::attr(href)',
            'a[href$=".ppt"]::attr(href)',
        ]
        doc_links = []
        for selector in doc_selectors:
            links = response.css(selector).getall()
            doc_links.extend(links)
            self.logger.debug(f"Found {len(links)} links with selector: {selector}")
        
        self.logger.info(f"Total document links found: {len(doc_links)}")
        
        if not doc_links:
            self.logger.warning("No document links found. Checking page content...")
            # Log some of the page content for debugging
            self.logger.debug(f"Page title: {response.css('title::text').get()}")
            self.logger.debug(f"First 500 chars: {response.text[:500]}")
        
        for link in doc_links:
            full_url = urljoin(response.url, link)
            self.logger.info(f"Queuing document: {full_url}")
            yield scrapy.Request(
                url=full_url,
                callback=self.save_document
            )

        # Look for more investor relations pages
        ir_links = response.css('a[href*="investor-relations/"]::attr(href)').getall()
    
        
        for link in ir_links[:self.num_pages]:  # Limit to avoid infinite crawling
            full_url = urljoin(response.url, link)
            if full_url != response.url:  # Avoid self-loops
                self.logger.info(f"Following IR link: {full_url}")
                yield scrapy.Request(url=full_url, callback=self.parse)


    def save_document(self, response):
        """Save the document to the local file system.
        Will create a directory structure based on the domain and save the file with its original name or a hash if no name is available.
        All documents are saved in the 'kb' directory."""
        
        self.logger.info(f"Downloading document from: {response.url}")
        
        parsed_url = urlparse(response.url)
        domain = parsed_url.netloc.replace("www.", "")
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = f"document_{hash(response.url) % 10000}.bin"
            
        os.makedirs(f'kb/{domain}', exist_ok=True)
        filepath = f'kb/{domain}/{filename}'
        
        with open(filepath, 'wb') as f:
            f.write(response.body)
        
        file_size = len(response.body)
        self.logger.info(f"Saved document: {filepath} ({file_size} bytes)")

if __name__ == '__main__':
    import sys
    
    start_urls = sys.argv[1] if len(sys.argv) > 1 else 'http://example.com/investor-relations'
    allowed_domains = sys.argv[2] if len(sys.argv) > 2 else 'example.com'
    
    process = CrawlerProcess({
        'LOG_LEVEL': 'INFO',
        'DOWNLOAD_DELAY': 1,
        'ROBOTSTXT_OBEY': True,
    })
    
    process.crawl(IRWebSpider, 
                  start_urls=start_urls, 
                  allowed_domains=allowed_domains)
    
    process.start()