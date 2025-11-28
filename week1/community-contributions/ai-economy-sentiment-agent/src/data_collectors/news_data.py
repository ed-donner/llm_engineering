"""
News article collection from Google News RSS feeds
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any

from config import RSS_FEEDS, MAX_ARTICLES_PER_CATEGORY, HEADERS


def get_news_articles() -> List[Dict[str, Any]]:
    """
    Fetch recent news articles from Google News RSS feeds.
    
    Returns:
        List of article dictionaries containing:
        - category: 'Economy' or 'Politics'
        - title: Article headline
        - source: Publisher name (CNN, Reuters, etc.)
        - description: Article summary/snippet
        - link: Article URL (Google News redirect)
        - pub_date: Publication date string
        - content: Combined source + description text
    """
    articles = []
    
    print("Fetching news articles...\n")
    
    for category, feed_url in RSS_FEEDS.items():
        try:
            print(f"Fetching {category} news...")
            response = requests.get(feed_url, headers=HEADERS, timeout=10)
            
            # Parse XML/RSS feed
            soup = None
            try:
                soup = BeautifulSoup(response.content, 'lxml-xml')
            except:
                try:
                    soup = BeautifulSoup(response.content, 'lxml')
                except:
                    soup = BeautifulSoup(response.content, 'html.parser')
            
            if not soup:
                print(f"  [ERROR] Could not parse feed")
                continue
            
            # Extract article items from RSS
            items = soup.find_all('item')[:MAX_ARTICLES_PER_CATEGORY]
            
            for item in items:
                try:
                    title = item.find('title').text if item.find('title') else 'No title'
                    link = item.find('link').text if item.find('link') else None
                    pub_date = item.find('pubDate').text if item.find('pubDate') else 'Unknown date'
                    
                    # Extract source (publisher)
                    source = ''
                    source_tag = item.find('source')
                    if source_tag:
                        source = source_tag.text.strip()
                    
                    # Extract description/summary
                    description = ''
                    desc_tag = item.find('description')
                    if desc_tag:
                        desc_soup = BeautifulSoup(desc_tag.text, 'html.parser')
                        description = desc_soup.get_text(strip=True)
                    
                    # Build content from RSS data
                    content_parts = []
                    if source:
                        content_parts.append(f"Source: {source}.")
                    if description:
                        content_parts.append(description)
                    
                    content = ' '.join(content_parts) if content_parts else title
                    
                    if link:
                        article = {
                            'category': category,
                            'title': title,
                            'source': source,
                            'description': description,
                            'content': content,
                            'link': link,
                            'pub_date': pub_date,
                            'scraped': False
                        }
                        articles.append(article)
                        print(f"  [OK] {title[:70]}...")
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"  [ERROR] Error fetching {category} news: {str(e)[:50]}")
    
    print(f"\n[OK] Found {len(articles)} articles total")
    return articles

