#!/usr/bin/env python3
"""
Simple NTSA Web Scraper with Selenium
A minimal scraper that handles JavaScript-rendered content
"""

import time
import json
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


def scrape_ntsa_page(url: str) -> dict:
    """Scrape a single NTSA page using Selenium"""
    driver = None
    try:
        # Setup Chrome driver
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Load page
        driver.get(url)
        time.sleep(3)  # Wait for JavaScript to load
        
        # Wait for content
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Get page source and parse
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "NTSA Page"
        
        # Extract main content
        content = soup.get_text().strip()
        
        return {
            'url': url,
            'title': title_text,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None
    finally:
        if driver:
            driver.quit()


def main():
    """Main scraping function"""
    print("🕷️ Simple NTSA Scraper")
    
    # Sample URLs to scrape
    urls = [
        "https://ntsa.go.ke",
        "https://ntsa.go.ke/about",
        "https://ntsa.go.ke/services"
    ]
    
    results = []
    output_dir = Path("sample_ntsa_data")
    output_dir.mkdir(exist_ok=True)
    
    for url in urls:
        print(f"Scraping: {url}")
        data = scrape_ntsa_page(url)
        if data:
            results.append(data)
            
            # Save to file
            safe_title = "".join(c for c in data['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')[:30]
            filename = f"ntsa_{safe_title}.md"
            filepath = output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {data['title']}\n\n")
                f.write(f"**URL:** {data['url']}\n")
                f.write(f"**Scraped:** {data['timestamp']}\n\n")
                f.write(data['content'][:1000] + "...")
    
    # Save metadata
    metadata = {
        'scraping_date': datetime.now().isoformat(),
        'total_pages': len(results),
        'pages': results
    }
    
    with open(output_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Scraped {len(results)} pages to {output_dir}")


if __name__ == "__main__":
    main()
