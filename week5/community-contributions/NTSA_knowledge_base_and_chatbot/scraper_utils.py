"""
scraper_utils.py
Web scraping utilities for NTSA knowledge base
"""

import requests
from bs4 import BeautifulSoup
import os
import json
import time
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
from datetime import datetime
import hashlib
import ssl
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NTSAKnowledgeBaseScraper:
    def __init__(self, base_url="https://ntsa.go.ke", output_dir="ntsa_knowledge_base"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.visited_urls = set()
        self.scraped_data = []
        
        # Category mapping based on URL patterns and content
        self.categories = {
            'driving_licenses': ['driving', 'license', 'dl', 'learner', 'provisional'],
            'vehicle_registration': ['registration', 'vehicle', 'logbook', 'number plate', 'transfer'],
            'road_safety': ['safety', 'inspection', 'accident', 'compliance'],
            'services': ['service', 'application', 'fee', 'payment', 'online'],
            'requirements': ['requirement', 'document', 'eligibility', 'criteria'],
            'procedures': ['procedure', 'process', 'step', 'how to', 'guide'],
            'about': ['about', 'contact', 'mission', 'vision', 'staff'],
            'news': ['news', 'announcement', 'press', 'notice'],
            'downloads': ['download', 'form', 'pdf', 'document'],
        }
        
        self.setup_directories()
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Create session with SSL handling
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Disable SSL verification for problematic sites
        self.session.verify = False
    
    def setup_directories(self):
        """Create folder structure for knowledge base"""
        self.output_dir.mkdir(exist_ok=True)
        
        for category in self.categories.keys():
            (self.output_dir / category).mkdir(exist_ok=True)
        
        (self.output_dir / 'metadata').mkdir(exist_ok=True)
        
        print(f"✓ Created directory structure in {self.output_dir}")
    
    def get_page(self, url, retries=3):
        """Fetch page content with retry logic and SSL handling"""
        for attempt in range(retries):
            try:
                # Try with session first (with SSL disabled)
                response = self.session.get(
                    url, 
                    headers=self.headers, 
                    timeout=15,
                    verify=False,
                    allow_redirects=True
                )
                response.raise_for_status()
                return response
                
            except requests.exceptions.SSLError as e:
                if attempt == retries - 1:
                    print(f"✗ SSL Error for {url}: {e}")
                    # Try with HTTP instead of HTTPS
                    http_url = url.replace('https://', 'http://')
                    try:
                        response = self.session.get(
                            http_url, 
                            headers=self.headers, 
                            timeout=15,
                            verify=False
                        )
                        response.raise_for_status()
                        print(f"✓ Successfully accessed via HTTP: {http_url}")
                        return response
                    except Exception as http_e:
                        print(f"✗ HTTP fallback failed for {http_url}: {http_e}")
                        return None
                else:
                    print(f"⚠️ SSL Error (attempt {attempt + 1}/{retries}): {e}")
                    time.sleep(2 ** attempt)
                    
            except requests.RequestException as e:
                if attempt == retries - 1:
                    print(f"✗ Failed to fetch {url}: {e}")
                    return None
                print(f"⚠️ Request failed (attempt {attempt + 1}/{retries}): {e}")
                time.sleep(2 ** attempt)
                
        return None
    
    def test_connection(self, url):
        """Test connection to a URL with various methods"""
        print(f"🔍 Testing connection to {url}...")
        
        # Test 1: HTTPS with SSL disabled
        try:
            response = self.session.get(url, timeout=10, verify=False)
            if response.status_code == 200:
                print(f"✓ HTTPS connection successful (SSL disabled)")
                return True
        except Exception as e:
            print(f"✗ HTTPS failed: {e}")
        
        # Test 2: HTTP fallback
        http_url = url.replace('https://', 'http://')
        try:
            response = self.session.get(http_url, timeout=10)
            if response.status_code == 200:
                print(f"✓ HTTP connection successful")
                return True
        except Exception as e:
            print(f"✗ HTTP failed: {e}")
        
        # Test 3: Try with different user agent
        try:
            old_headers = self.session.headers.copy()
            self.session.headers.update({
                'User-Agent': 'curl/7.68.0'
            })
            response = self.session.get(url, timeout=10, verify=False)
            if response.status_code == 200:
                print(f"✓ Connection successful with curl user agent")
                self.session.headers.update(old_headers)
                return True
            self.session.headers.update(old_headers)
        except Exception as e:
            print(f"✗ Curl user agent failed: {e}")
        
        print(f"✗ All connection methods failed for {url}")
        return False
    
    def get_alternative_urls(self, base_url):
        """Get alternative URLs to try if the main URL fails"""
        alternatives = [
            base_url,
            base_url.replace('https://', 'http://'),
            f"{base_url}/index.php",
            f"{base_url}/index.html",
            f"{base_url}/home",
            f"{base_url}/main"
        ]
        return list(set(alternatives))  # Remove duplicates
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\-.,;:!?()\[\]"\'/]', '', text)
        return text.strip()
    
    def categorize_content(self, url, title, content):
        """Determine category based on URL and content"""
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()
        
        category_scores = {}
        for category, keywords in self.categories.items():
            score = 0
            for keyword in keywords:
                if keyword in url_lower:
                    score += 5
                if keyword in title_lower:
                    score += 3
                if keyword in content_lower:
                    score += 1
            category_scores[category] = score
        
        best_category = max(category_scores, key=category_scores.get)
        return best_category if category_scores[best_category] > 0 else 'services'
    
    def extract_links(self, soup, current_url):
        """Extract all relevant links from page"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            
            if urlparse(full_url).netloc == urlparse(self.base_url).netloc:
                if not any(full_url.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.jpg', '.png']):
                    if '#' in full_url:
                        full_url = full_url.split('#')[0]
                    links.append(full_url)
        
        return list(set(links))
    
    def extract_content(self, soup, url):
        """Extract main content from page with improved logic"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        main_content = None
        content_selectors = [
            'main', 'article', '.content', '#content', 
            '.main-content', '#main-content', '.post-content',
            '.entry-content', 'div[role="main"]',
            '.container', '.wrapper', '#main', '.main',
            'body'  # Fallback to body if no specific content area found
        ]
        
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.body
        
        if not main_content:
            return ""
        
        content_parts = []
        # Look for more element types
        for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'td', 'div', 'span']):
            text = self.clean_text(element.get_text())
            if text and len(text) > 5:  # Reduced minimum length
                content_parts.append(text)
        
        # If no content found with specific elements, try getting all text
        if not content_parts:
            all_text = self.clean_text(main_content.get_text())
            if all_text and len(all_text) > 10:
                content_parts.append(all_text)
        
        return ' '.join(content_parts)
    
    def create_markdown(self, title, url, content, category, metadata):
        """Create markdown document"""
        filename_base = re.sub(r'[^\w\s-]', '', title.lower())
        filename_base = re.sub(r'[-\s]+', '_', filename_base)[:50]
        
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"{filename_base}_{url_hash}.md"
        
        md_content = f"""# {title}

**Source:** [{url}]({url})  
**Category:** {category}  
**Scraped:** {metadata['scraped_date']}  

---

## Content

{content}

---

## Metadata
- **Word Count:** {metadata['word_count']}
- **URL:** {url}
- **Category:** {category}
"""
        
        filepath = self.output_dir / category / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return filepath
    
    def scrape_page(self, url, depth=0, max_depth=3):
        """Scrape a single page and follow links"""
        if depth > max_depth or url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        print(f"{'  ' * depth}📄 Scraping: {url}")
        
        response = self.get_page(url)
        if not response:
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.title.string if soup.title else url.split('/')[-1]
        title = self.clean_text(title)
        
        content = self.extract_content(soup, url)
        
        if len(content) < 50:
            print(f"{'  ' * depth}  ⊘ Skipped (insufficient content: {len(content)} chars)")
            print(f"{'  ' * depth}  📝 Content preview: {content[:100]}...")
            return
        
        category = self.categorize_content(url, title, content)
        
        metadata = {
            'url': url,
            'title': title,
            'category': category,
            'scraped_date': datetime.now().isoformat(),
            'word_count': len(content.split()),
            'depth': depth
        }
        
        filepath = self.create_markdown(title, url, content, category, metadata)
        print(f"{'  ' * depth}  ✓ Saved to {category}/{filepath.name}")
        
        self.scraped_data.append(metadata)
        
        time.sleep(1)
        
        if depth < max_depth:
            links = self.extract_links(soup, url)
            for link in links[:10]:
                if link not in self.visited_urls:
                    self.scrape_page(link, depth + 1, max_depth)
    
    def save_metadata(self):
        """Save scraping metadata to JSON"""
        metadata_file = self.output_dir / 'metadata' / 'scraping_metadata.json'
        
        summary = {
            'scraping_date': datetime.now().isoformat(),
            'total_pages': len(self.scraped_data),
            'categories': {},
            'pages': self.scraped_data
        }
        
        for page in self.scraped_data:
            category = page['category']
            summary['categories'][category] = summary['categories'].get(category, 0) + 1
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n✓ Metadata saved to {metadata_file}")
        return summary
    
    def create_index(self):
        """Create an index markdown file"""
        index_content = f"""# NTSA Knowledge Base Index

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Documents:** {len(self.scraped_data)}

---

## Categories

"""
        by_category = {}
        for page in self.scraped_data:
            category = page['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(page)
        
        for category, pages in sorted(by_category.items()):
            index_content += f"\n### {category.replace('_', ' ').title()} ({len(pages)} documents)\n\n"
            for page in sorted(pages, key=lambda x: x['title']):
                filename_base = re.sub(r'[^\w\s-]', '', page['title'].lower())
                filename_base = re.sub(r'[-\s]+', '_', filename_base)[:50]
                url_hash = hashlib.md5(page['url'].encode()).hexdigest()[:8]
                filename = f"{filename_base}_{url_hash}.md"
                
                index_content += f"- [{page['title']}](./{category}/{filename})\n"
        
        index_file = self.output_dir / 'INDEX.md'
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print(f"✓ Index created at {index_file}")
    
    def run(self, start_urls=None, max_depth=2):
        """Run the complete scraping process"""
        print("="*60)
        print("NTSA Knowledge Base Scraper")
        print("="*60)
        
        if start_urls is None:
            start_urls = [self.base_url]
        
        print(f"\nStarting scraping from {len(start_urls)} URL(s)...")
        print(f"Max depth: {max_depth}\n")
        
        # Test connections first and try alternatives
        working_urls = []
        for url in start_urls:
            if self.test_connection(url):
                working_urls.append(url)
            else:
                print(f"⚠️ Main URL failed, trying alternatives...")
                alternatives = self.get_alternative_urls(url)
                found_working = False
                for alt_url in alternatives:
                    if alt_url != url and self.test_connection(alt_url):
                        working_urls.append(alt_url)
                        found_working = True
                        print(f"✅ Found working alternative: {alt_url}")
                        break
                
                if not found_working:
                    print(f"❌ All alternatives failed for {url}")
        
        if not working_urls:
            print("❌ No working URLs found. Please check your internet connection and the website availability.")
            return None
        
        print(f"\n✅ Found {len(working_urls)} working URL(s). Starting scraping...\n")
        
        for url in working_urls:
            self.scrape_page(url, depth=0, max_depth=max_depth)
        
        print("\n" + "="*60)
        print("Finalizing knowledge base...")
        print("="*60)
        
        summary = self.save_metadata()
        self.create_index()
        
        print("\n" + "="*60)
        print("SCRAPING COMPLETE!")
        print("="*60)
        print(f"\nTotal pages scraped: {len(self.scraped_data)}")
        print(f"Output directory: {self.output_dir.absolute()}")
        print("\nPages by category:")
        for category, count in sorted(summary['categories'].items()):
            print(f"  - {category.replace('_', ' ').title()}: {count}")
        
        return summary
