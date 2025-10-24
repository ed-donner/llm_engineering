#!/usr/bin/env python3
"""
Simple Comprehensive Selenium Scraper for NTSA Website
A simplified, working version of the comprehensive scraper
"""

import os
import json
import time
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set, Optional
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


class SimpleComprehensiveScraper:
    """Simple comprehensive scraper for NTSA website"""
    
    def __init__(self, base_url: str = "https://ntsa.go.ke", output_dir: str = "ntsa_comprehensive_knowledge_base", 
                 wait_time: int = 10, page_load_sleep: int = 3, link_follow_limit: int = 10, 
                 min_content_length: int = 50):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.wait_time = wait_time
        self.page_load_sleep = page_load_sleep
        self.link_follow_limit = link_follow_limit
        self.min_content_length = min_content_length
        
        # Create output directory structure
        self._create_directory_structure()
        
        # Initialize tracking
        self.scraped_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.scraped_data: List[Dict] = []
        
        # Initialize driver
        self.driver = None
        
    def _create_directory_structure(self):
        """Create the output directory structure"""
        directories = [
            'about', 'services', 'news', 'tenders', 'careers', 'downloads',
            'driving_licenses', 'vehicle_registration', 'road_safety', 
            'procedures', 'requirements', 'raw_html', 'screenshots', 'metadata'
        ]
        
        for directory in directories:
            (self.output_dir / directory).mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Created directory structure in {self.output_dir}")
    
    def _setup_driver(self):
        """Setup Chrome driver with options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            
            print("✅ Chrome driver initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            return False
    
    def _get_page_content(self, url: str) -> Optional[Dict]:
        """Get page content using Selenium"""
        try:
            print(f"🌐 Loading: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(self.page_load_sleep)
            
            # Wait for content to be present
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "NTSA Page"
            
            # Extract main content
            content_selectors = [
                'main', 'article', '.content', '#content', '.main-content',
                '.page-content', '.post-content', '.entry-content'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = " ".join([elem.get_text().strip() for elem in elements])
                    break
            
            # If no specific content found, get all text
            if not content or len(content) < self.min_content_length:
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                content = soup.get_text()
            
            # Clean content
            content = content.strip()
            
            if len(content) < self.min_content_length:
                print(f"⚠️ Content too short ({len(content)} chars): {url}")
                return None
            
            return {
                'url': url,
                'title': title_text,
                'content': content,
                'html': page_source,
                'timestamp': datetime.now().isoformat(),
                'content_length': len(content)
            }
            
        except TimeoutException:
            print(f"⏰ Timeout loading: {url}")
            return None
        except WebDriverException as e:
            print(f"🚫 WebDriver error for {url}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error processing {url}: {e}")
            return None
    
    def _extract_links_from_page(self, url: str) -> List[str]:
        """Extract links from the current page"""
        try:
            # Wait for page to load
            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Find all links
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            extracted_links = []
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href:
                        # Convert relative URLs to absolute
                        absolute_url = urljoin(url, href)
                        parsed_url = urlparse(absolute_url)
                        
                        # Only include links from the same domain
                        if parsed_url.netloc == urlparse(self.base_url).netloc:
                            extracted_links.append(absolute_url)
                            
                except Exception as e:
                    continue
            
            return list(set(extracted_links))  # Remove duplicates
            
        except Exception as e:
            print(f"❌ Error extracting links from {url}: {e}")
            return []
    
    def _save_content(self, content_data: Dict) -> str:
        """Save content to file and return file path"""
        try:
            # Generate filename from URL
            url_hash = hashlib.md5(content_data['url'].encode()).hexdigest()[:8]
            safe_title = "".join(c for c in content_data['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:50]
            filename = f"ntsa_{safe_title}_{url_hash}.md"
            
            # Determine category based on URL
            category = self._categorize_url(content_data['url'])
            category_dir = self.output_dir / category
            category_dir.mkdir(exist_ok=True)
            
            # Save markdown content
            md_file = category_dir / filename
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(f"# {content_data['title']}\n\n")
                f.write(f"**URL:** {content_data['url']}\n")
                f.write(f"**Scraped:** {content_data['timestamp']}\n")
                f.write(f"**Content Length:** {content_data['content_length']} characters\n\n")
                f.write("---\n\n")
                f.write(content_data['content'])
            
            # Save raw HTML
            html_file = self.output_dir / 'raw_html' / f"{safe_title}_{url_hash}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(content_data['html'])
            
            return str(md_file)
            
        except Exception as e:
            print(f"❌ Error saving content: {e}")
            return ""
    
    def _categorize_url(self, url: str) -> str:
        """Categorize URL based on path"""
        url_lower = url.lower()
        
        if '/about' in url_lower:
            return 'about'
        elif '/services' in url_lower:
            return 'services'
        elif '/news' in url_lower or '/media' in url_lower:
            return 'news'
        elif '/tenders' in url_lower:
            return 'tenders'
        elif '/careers' in url_lower or '/jobs' in url_lower:
            return 'careers'
        elif '/downloads' in url_lower:
            return 'downloads'
        elif '/driving' in url_lower or '/license' in url_lower:
            return 'driving_licenses'
        elif '/vehicle' in url_lower or '/registration' in url_lower:
            return 'vehicle_registration'
        elif '/safety' in url_lower or '/road' in url_lower:
            return 'road_safety'
        elif '/procedures' in url_lower:
            return 'procedures'
        elif '/requirements' in url_lower:
            return 'requirements'
        else:
            return 'services'  # Default category
    
    def scrape_comprehensive(self, start_urls: List[str], max_pages: int = 50, max_depth: int = 3) -> List[Dict]:
        """Comprehensive scraping of NTSA website"""
        print("🚀 Starting comprehensive NTSA scraping...")
        print(f"📋 Starting URLs: {len(start_urls)}")
        print(f"📄 Max pages: {max_pages}")
        print(f"🔍 Max depth: {max_depth}")
        
        if not self._setup_driver():
            print("❌ Failed to initialize driver. Cannot proceed.")
            return []
        
        try:
            # Initialize queue with start URLs
            url_queue = [(url, 0) for url in start_urls]  # (url, depth)
            processed_count = 0
            
            while url_queue and processed_count < max_pages:
                current_url, depth = url_queue.pop(0)
                
                # Skip if already processed or too deep
                if current_url in self.scraped_urls or depth > max_depth:
                    continue
                
                print(f"\n📄 Processing ({processed_count + 1}/{max_pages}): {current_url}")
                print(f"🔍 Depth: {depth}")
                
                # Get page content
                content_data = self._get_page_content(current_url)
                
                if content_data:
                    # Save content
                    file_path = self._save_content(content_data)
                    if file_path:
                        self.scraped_urls.add(current_url)
                        self.scraped_data.append({
                            'url': current_url,
                            'title': content_data['title'],
                            'file_path': file_path,
                            'category': self._categorize_url(current_url),
                            'content_length': content_data['content_length'],
                            'depth': depth
                        })
                        print(f"✅ Saved: {file_path}")
                        print(f"📊 Content: {content_data['content_length']} chars")
                        
                        # Extract links for further crawling (if not at max depth)
                        if depth < max_depth:
                            links = self._extract_links_from_page(current_url)
                            new_links = [link for link in links if link not in self.scraped_urls and link not in self.failed_urls]
                            
                            # Limit new links to avoid infinite crawling
                            new_links = new_links[:self.link_follow_limit]
                            
                            if new_links:
                                print(f"🔗 Found {len(new_links)} new links")
                                for link in new_links:
                                    url_queue.append((link, depth + 1))
                            else:
                                print("🔗 No new links found")
                    else:
                        print(f"❌ Failed to save content for: {current_url}")
                        self.failed_urls.add(current_url)
                else:
                    print(f"❌ Failed to get content for: {current_url}")
                    self.failed_urls.add(current_url)
                
                processed_count += 1
                
                # Small delay between requests
                time.sleep(1)
            
            # Save metadata
            self._save_metadata()
            
            print(f"\n🎉 Comprehensive scraping completed!")
            print(f"📊 Total pages scraped: {len(self.scraped_data)}")
            print(f"❌ Failed pages: {len(self.failed_urls)}")
            print(f"📁 Output directory: {self.output_dir.absolute()}")
            
            return self.scraped_data
            
        except Exception as e:
            print(f"❌ Error during comprehensive scraping: {e}")
            return []
        
        finally:
            if self.driver:
                self.driver.quit()
                print("🔚 Driver closed")
    
    def _save_metadata(self):
        """Save scraping metadata"""
        try:
            metadata = {
                'scraping_info': {
                    'base_url': self.base_url,
                    'total_pages_scraped': len(self.scraped_data),
                    'failed_pages': len(self.failed_urls),
                    'scraping_timestamp': datetime.now().isoformat(),
                    'output_directory': str(self.output_dir)
                },
                'scraped_pages': self.scraped_data,
                'failed_urls': list(self.failed_urls)
            }
            
            metadata_file = self.output_dir / 'metadata' / 'comprehensive_metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Create index file
            self._create_index_file()
            
            print(f"✅ Metadata saved to {metadata_file}")
            
        except Exception as e:
            print(f"❌ Error saving metadata: {e}")
    
    def _create_index_file(self):
        """Create an index file of all scraped content"""
        try:
            index_file = self.output_dir / 'INDEX.md'
            
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write("# NTSA Knowledge Base Index\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Total Pages:** {len(self.scraped_data)}\n\n")
                
                # Group by category
                categories = {}
                for item in self.scraped_data:
                    category = item['category']
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(item)
                
                for category, items in categories.items():
                    f.write(f"## {category.title()}\n\n")
                    for item in items:
                        f.write(f"- [{item['title']}]({item['file_path']})\n")
                        f.write(f"  - URL: {item['url']}\n")
                        f.write(f"  - Content: {item['content_length']} chars\n")
                        f.write(f"  - Depth: {item['depth']}\n\n")
            
            print(f"✅ Index file created: {index_file}")
            
        except Exception as e:
            print(f"❌ Error creating index file: {e}")


def main():
    """Main function to run the scraper"""
    print("🚀 NTSA Comprehensive Scraper")
    print("=" * 50)
    
    # Configuration
    config = {
        'base_url': 'https://ntsa.go.ke',
        'start_urls': [
            'https://ntsa.go.ke',
            'https://ntsa.go.ke/about',
            'https://ntsa.go.ke/services',
            'https://ntsa.go.ke/contact',
            'https://ntsa.go.ke/news',
            'https://ntsa.go.ke/tenders'
        ],
        'output_dir': 'ntsa_comprehensive_knowledge_base',
        'max_pages': 100,
        'max_depth': 3,
        'wait_time': 10,
        'page_load_sleep': 3,
        'link_follow_limit': 10,
        'min_content_length': 50
    }
    
    # Initialize scraper
    scraper = SimpleComprehensiveScraper(
        base_url=config['base_url'],
        output_dir=config['output_dir'],
        wait_time=config['wait_time'],
        page_load_sleep=config['page_load_sleep'],
        link_follow_limit=config['link_follow_limit'],
        min_content_length=config['min_content_length']
    )
    
    # Run scraping
    result = scraper.scrape_comprehensive(
        start_urls=config['start_urls'],
        max_pages=config['max_pages'],
        max_depth=config['max_depth']
    )
    
    if result:
        print(f"\n✅ Scraping completed successfully!")
        print(f"📊 Total pages scraped: {len(result)}")
    else:
        print("\n❌ Scraping failed or no pages were scraped.")


if __name__ == "__main__":
    main()