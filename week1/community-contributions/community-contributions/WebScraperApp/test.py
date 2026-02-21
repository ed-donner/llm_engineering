#!/usr/bin/env python3
"""
Simple test script to verify the web scraping functionality
"""

import module

def test_basic_scraping():
    """Test basic scraping functionality"""
    print("Testing basic web scraping...")
    
    # Create a scraper instance
    scraper = module.WebScraper()
    
    # Test with a simple website (httpbin.org is a safe test site)
    test_url = "https://httpbin.org/html"
    
    print(f"Scraping {test_url} with depth 1...")
    
    try:
        # Scrape with depth 1 to keep it fast
        websites = scraper.crawl_website(test_url, max_depth=1)
        
        print(f"Successfully scraped {len(websites)} websites")
        
        if websites:
            # Show first website details
            first_site = websites[0]
            print(f"\nFirst website:")
            print(f"  Title: {first_site.title}")
            print(f"  URL: {first_site.url}")
            print(f"  Depth: {first_site.depth}")
            print(f"  Links found: {len(first_site.links)}")
            print(f"  Word count: {first_site.get_word_count()}")
            
            # Show statistics
            stats = scraper.get_statistics()
            print(f"\nStatistics:")
            print(f"  Total pages: {stats['total_pages']}")
            print(f"  Total links: {stats['total_links']}")
            print(f"  Total words: {stats['total_words']}")
            print(f"  Average load time: {stats['avg_load_time']:.2f}s")
            
            return True
        else:
            print("No websites were scraped")
            return False
            
    except Exception as e:
        print(f"Error during scraping: {e}")
        return False

def test_website_class():
    """Test the Website class functionality"""
    print("\nTesting Website class...")
    
    # Create a test website
    website = module.Website(
        title="Test Website",
        url="https://example.com",
        content="<html><body><h1>Test Content</h1><p>This is a test paragraph.</p></body></html>",
        depth=0,
        links=["https://example.com/page1", "https://example.com/page2"]
    )
    
    # Test methods
    print(f"Website title: {website.title}")
    print(f"Website URL: {website.url}")
    print(f"Word count: {website.get_word_count()}")
    print(f"Domain: {website.get_domain()}")
    print(f"Normalized domain: {website.get_normalized_domain()}")
    print(f"Search for 'test': {website.search_content('test')}")
    print(f"Search for 'nonexistent': {website.search_content('nonexistent')}")
    
    return True

def test_html_parser():
    """Test the HTML parser functionality"""
    print("\nTesting HTML Parser...")
    
    parser = module.HTMLParser()
    test_html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Welcome</h1>
            <p>This is a <a href="https://example.com">link</a> to example.com</p>
            <p>Here's another <a href="/relative-link">relative link</a></p>
        </body>
    </html>
    """
    
    parser.feed(test_html)
    print(f"Title extracted: {parser.title}")
    print(f"Links found: {parser.links}")
    print(f"Text content length: {len(parser.get_text())}")
    
    return True

def test_url_normalization():
    """Test URL normalization to handle www. prefixes"""
    print("\nTesting URL Normalization...")
    
    scraper = module.WebScraper()
    
    # Test URLs with and without www.
    test_urls = [
        "https://www.example.com/page",
        "https://example.com/page",
        "http://www.test.com/path?param=value#fragment",
        "http://test.com/path?param=value#fragment"
    ]
    
    print("URL Normalization Results:")
    for url in test_urls:
        normalized = scraper.normalize_url(url)
        print(f"  Original: {url}")
        print(f"  Normalized: {normalized}")
        print()
    
    # Test domain filtering
    print("Domain Filtering Test:")
    test_websites = [
        module.Website("Site 1", "https://www.example.com", "content", 0),
        module.Website("Site 2", "https://example.com", "content", 0),
        module.Website("Site 3", "https://www.test.com", "content", 0)
    ]
    
    scraper.websites = test_websites
    
    # Test filtering by domain with and without www.
    domains_to_test = ["example.com", "www.example.com", "test.com", "www.test.com"]
    
    for domain in domains_to_test:
        filtered = scraper.filter_by_domain(domain)
        print(f"  Filter '{domain}': {len(filtered)} results")
        for site in filtered:
            print(f"    - {site.title} ({site.url})")
    
    return True

if __name__ == "__main__":
    print("Web Scraper Test Suite")
    print("=" * 50)
    
    # Test HTML parser
    test_html_parser()
    
    # Test Website class
    test_website_class()
    
    # Test URL normalization
    test_url_normalization()
    
    # Test basic scraping (uncomment to test actual scraping)
    # Note: This requires internet connection
    # test_basic_scraping()
    
    print("\nTest completed!")
    print("\nTo run the full application:")
    print("python web_scraper_app.py") 