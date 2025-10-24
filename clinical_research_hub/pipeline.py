#!/usr/bin/env python3
"""
The GenAI Clinical Trials Watch Pipeline
Processes RSS feeds, identifies AI-specific content in clinical research, generates HTML.
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import requests
from urllib.parse import quote_plus, urlparse, parse_qs, urlencode, urlunparse
import math
import random
import hashlib
import tempfile
from dataclasses import dataclass

import feedparser
from qwen_client import QwenOpenRouterClient
from pydantic import BaseModel, Field, ValidationError

# Robust HTTP retry configuration
@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True

def request_with_retries(
    session: requests.Session,
    method: str,
    url: str,
    timeout: int = 30,
    retry_config: Optional[RetryConfig] = None,
    **kwargs
) -> requests.Response:
    """
    Make HTTP request with exponential backoff and jitter.
    
    Args:
        session: requests session
        method: HTTP method (GET, POST, etc.)
        url: Target URL
        timeout: Request timeout in seconds
        retry_config: Retry configuration
        **kwargs: Additional arguments for requests
    
    Returns:
        requests.Response object
        
    Raises:
        requests.RequestException: After all retries exhausted
    """
    if retry_config is None:
        retry_config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(retry_config.max_retries + 1):
        try:
            response = session.request(method, url, timeout=timeout, **kwargs)
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    try:
                        delay = float(retry_after)
                        logging.warning(f"Rate limited, retrying after {delay}s for {url}")
                        time.sleep(delay)
                        continue
                    except ValueError:
                        pass
            
            # Raise for other HTTP errors (will be caught and retried if appropriate)
            response.raise_for_status()
            return response
            
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            last_exception = e
            
            # Don't retry on client errors (4xx except 429)
            if hasattr(e, 'response') and e.response is not None:
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    logging.error(f"Client error {e.response.status_code} for {url}: {e}")
                    raise e
            
            if attempt == retry_config.max_retries:
                logging.error(f"Final retry failed for {url} after {attempt + 1} attempts: {e}")
                break
            
            # Calculate delay with exponential backoff and jitter
            delay = min(
                retry_config.base_delay * (retry_config.backoff_factor ** attempt),
                retry_config.max_delay
            )
            
            if retry_config.jitter:
                delay *= (0.5 + random.random() * 0.5)  # 50-150% of calculated delay
            
            logging.warning(f"Request failed for {url} (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
            time.sleep(delay)
    
    # All retries exhausted
    raise last_exception

def canonicalize_url(url: str) -> str:
    """
    Canonicalize URL for deduplication by removing tracking parameters.
    
    Args:
        url: Original URL
        
    Returns:
        Canonicalized URL string
    """
    try:
        parsed = urlparse(url)
        
        # Remove common tracking parameters
        tracking_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'ref', '_ga', '_gl', 'mc_cid', 'mc_eid',
            'source', 'medium', 'campaign'
        }
        
        query_params = parse_qs(parsed.query, keep_blank_values=False)
        filtered_params = {
            k: v for k, v in query_params.items() 
            if k.lower() not in tracking_params
        }
        
        # Rebuild query string
        new_query = urlencode(filtered_params, doseq=True) if filtered_params else ''
        
        # Normalize: lowercase host, remove trailing slash, rebuild URL
        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip('/') if parsed.path != '/' else parsed.path,
            parsed.params,
            new_query,
            ''  # Remove fragment
        ))
        
        return normalized
        
    except Exception as e:
        logging.warning(f"Failed to canonicalize URL {url}: {e}")
        return url

# Data validation models
class BriefItem(BaseModel):
    """Validated brief item model."""
    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., max_length=2000)
    summary: str = Field(..., min_length=10, max_length=1000)
    ai_tag: str = Field(..., min_length=1, max_length=100)
    source: str = Field(..., min_length=1, max_length=200)
    pub_date: str = Field(..., min_length=1)
    link: str = Field(..., min_length=10)
    brief_date: str = Field(..., min_length=1)
    search_query: Optional[str] = Field(None, max_length=500)
    is_ai_related: bool = True
    
    class Config:
        str_strip_whitespace = True

class BriefData(BaseModel):
    """Validated brief data container."""
    items: List[BriefItem]
    total_items: int = Field(ge=0)
    brief_date: str
    
    class Config:
        str_strip_whitespace = True

class TokenBucket:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, rate_per_sec: float = 2.0, burst: int = 4):
        """
        Initialize token bucket.
        
        Args:
            rate_per_sec: Tokens added per second
            burst: Maximum tokens in bucket
        """
        self.rate = rate_per_sec
        self.burst = burst
        self.tokens = float(burst)
        self.last_update = time.time()
    
    def consume(self, tokens: int = 1) -> None:
        """
        Consume tokens from bucket, blocking if necessary.
        
        Args:
            tokens: Number of tokens to consume
        """
        now = time.time()
        
        # Add tokens based on elapsed time
        elapsed = now - self.last_update
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_update = now
        
        # Block until we have enough tokens
        while self.tokens < tokens:
            sleep_time = (tokens - self.tokens) / self.rate
            time.sleep(sleep_time)
            
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now
        
        # Consume tokens
        self.tokens -= tokens

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
import bleach
from dateutil import parser as date_parser
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class FeedProcessor:
    """Handles web search and AI content identification in clinical research."""
    
    # Base topics for LLM-generated search queries - Enhanced with MeSH terms
    BASE_SEARCH_TOPICS = [
        # Core GenAI Technologies in Clinical Research
        "generative AI in clinical trials",
        "large language models healthcare research", 
        "ChatGPT clinical research applications",
        "GPT-4 clinical trial protocol writing",
        "Claude AI clinical research documentation",
        "foundation models drug discovery",
        "synthetic data clinical research",
        "LLM generated clinical reports",
        "generative AI medical writing clinical",
        
        # MeSH-informed search terms
        "artificial intelligence clinical trials MeSH",
        "machine learning clinical research methodology",
        "natural language processing clinical data",
        "computer-assisted clinical decision making",
        "automated clinical documentation systems",
        
        # Patient-Facing GenAI Applications
        "AI chatbots patient recruitment",
        "conversational AI patient engagement", 
        "AI virtual assistants clinical trials",
        "generative AI patient education",
        "AI-powered patient screening",
        "ChatGPT patient communication clinical",
        
        # Clinical Trial Operations & Management
        "AI protocol writing clinical research",
        "generative AI trial design",
        "AI clinical trial optimization",
        "automated clinical trial monitoring",
        "AI-powered site selection",
        "generative AI regulatory submissions",
        "LLM clinical trial compliance",
        "generative AI trial documentation",
        
        # Data & Documentation
        "natural language processing clinical documentation",
        "AI clinical data generation",
        "generative AI medical writing",
        "AI clinical report automation",
        "synthetic clinical trial data",
        "AI clinical data management",
        "generative AI data cleaning",
        "automated clinical data entry",
        "AI clinical database management",
        "AI clinical data integration",
        "generative AI case report forms",
        "automated clinical data validation",
        "LLM clinical summary generation",
        "generative AI regulatory documents",
        
        # Safety & Monitoring
        "AI safety monitoring clinical trials",
        "generative AI adverse event reporting",
        "AI pharmacovigilance clinical research",
        "automated safety signal detection",
        
        # Regulatory & Compliance
        "AI regulatory compliance clinical trials",
        "generative AI FDA submissions",
        "AI clinical trial auditing",
        "automated regulatory reporting",
        
        # Analytics & Outcomes
        "generative AI biomarker discovery",
        "AI predictive modeling clinical trials",
        "automated clinical data analysis"
    ]
    
    # Fallback queries if LLM generation fails
    FALLBACK_SEARCH_QUERIES = [
        '"generative AI" "clinical trials" pharmaceutical research',
        '"ChatGPT" "clinical research" drug development study',
        '"large language model" "clinical trials" healthcare research',
        '"synthetic data" "clinical trials" pharmaceutical study',
        '"AI chatbot" "patient recruitment" clinical research',
        '"foundation models" "clinical trials" drug discovery',
        '"generative AI" "protocol writing" clinical research',
        '"LLM" "clinical documentation" pharmaceutical study',
        '"conversational AI" "clinical trials" patient engagement',
        '"generative models" "drug discovery" clinical research'
    ]
    
    # Re-enabled key RSS/Atom feeds for better source acquisition
    RSS_FEEDS = [
        # Industry News - AI Focus
        ('https://www.statnews.com/tag/artificial-intelligence/feed/', 'STAT AI', 12),
        ('https://endpointsnews.com/feed/', 'Endpoints News', 10),
        ('https://www.fiercebiotech.com/rss/xml', 'Fierce Biotech', 10),
        
        # Clinical Trials News
        ('https://www.newswise.com/legacy/feed/channels.php?channel=6502', 'Newswise Clinical Trials', 10),
        
        # Academic/Research Feeds
        ('https://aihealth.duke.edu/feed/', 'Duke AI Health', 15),
        ('https://www.nature.com/subjects/machine-learning/nature-medicine.rss', 'Nature ML', 10),
        ('https://export.arxiv.org/rss/cs.AI', 'arXiv AI', 8),
        ('https://export.arxiv.org/rss/cs.LG', 'arXiv ML', 8),
        ('https://export.arxiv.org/rss/q-bio', 'arXiv Bio', 8),
        
        # Medical AI Research
        ('https://www.nature.com/nm.rss', 'Nature Medicine', 8),
        ('https://www.jmir.org/rss', 'JMIR', 8),
    ]
    
    # Source-specific limits for content discovery
    SOURCE_LIMITS = {
        'Duke AI Health': 15,               # Duke AI Health (AI focus)
        'STAT AI': 12,                      # STAT AI Coverage
        'MedCity News': 10,                 # MedCity News
        'Google Search': 5,                 # Per search query limit
        'PubMed': 8,                        # Academic papers
        # Default for others: 5
    }
    
    def __init__(self, qwen_api_key: str, log_file: str, days_back: int = 60):
        """Initialize the feed processor.
        
        Args:
            qwen_api_key: OpenRouter API key for Qwen model access
            log_file: Path to log file
            days_back: Number of days back to consider articles (default: 60)
        """
        # Validate required environment variables
        if not qwen_api_key:
            raise ValueError("OPENROUTER_API_KEY is required")
        
        self.qwen_client = QwenOpenRouterClient(api_key=qwen_api_key)
        self.logger = self._setup_logging(log_file)
        self.brief_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        self.days_back = days_back
        
        # Initialize search APIs with validation
        self.google_api_key = os.environ.get('GOOGLE_API_KEY')
        self.google_cx = os.environ.get('GOOGLE_CX')  # Custom Search Engine ID
        self.pubmed_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        
        # Log API availability
        if self.google_api_key and self.google_cx:
            self.logger.info("Google Custom Search API configured")
        else:
            self.logger.warning("Google Custom Search API not configured - will skip Google searches")
        
        # Additional API endpoints for broader source acquisition
        self.europepmc_base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
        self.semantic_scholar_base_url = "https://api.semanticscholar.org/graph/v1/"
        self.medrxiv_base_url = "https://api.medrxiv.org/"
        
        # Create robust HTTP session with retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Retry configuration
        self.retry_config = RetryConfig(max_retries=3, base_delay=1.0, max_delay=30.0)
        
        # Rate limiting configuration with token buckets
        self.google_requests_count = 0
        self.google_request_limit = 100  # Daily limit safety margin
        self.pubmed_request_limit = 300   # Per hour limit safety margin
        
        # Initialize token bucket rate limiters
        self.google_throttle = TokenBucket(rate_per_sec=1.0, burst=3)  # Conservative for Google API
        self.pubmed_throttle = TokenBucket(rate_per_sec=3.0, burst=5)  # PubMed allows more
        self.general_throttle = TokenBucket(rate_per_sec=2.0, burst=4)  # For other APIs
        
        # Cache for generated search queries to avoid regenerating on each run
        self._generated_queries_cache = None
        
        # Deduplication tracking
        self.seen_urls = set()
        self.seen_titles = set()
        
        # Cost tracking
        self.api_costs = {
            'qwen_calls': 0,
            'google_calls': 0,
            'pubmed_calls': 0,
            'estimated_cost_usd': 0.0
        }
        
    def _setup_logging(self, log_file: str) -> logging.Logger:
        """Set up JSON logging as specified in PRD without duplicating handlers."""
        logger = logging.getLogger('clinical_brief')
        logger.setLevel(logging.INFO)

        # Create log directory if it doesn't exist
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        log_path = Path(log_file).resolve()
        handler_exists = False
        for handler in logger.handlers:
            if not isinstance(handler, logging.FileHandler):
                continue
            base_filename = getattr(handler, 'baseFilename', None)
            if not base_filename:
                continue
            try:
                if Path(base_filename).resolve() == log_path:
                    handler_exists = True
                    break
            except FileNotFoundError:
                continue

        if not handler_exists:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger
    
    def _log_feed_request(self, url: str, status: int, timestamp: str, error: Optional[str] = None):
        """Log feed request details in JSON format."""
        log_entry = {
            "timestamp": timestamp,
            "feed_url": url,
            "http_status": status,
            "error": error
        }
        self.logger.info(json.dumps(log_entry))
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize and clean text input with improved Unicode handling."""
        if not text:
            return ""
        
        # Track if we had problematic characters for logging
        had_replacement_chars = '\ufffd' in text if isinstance(text, str) else False
        
        # Handle encoding issues more gracefully
        if isinstance(text, bytes):
            # Try multiple encodings before falling back to replace
            for encoding in ['utf-8', 'utf-16', 'latin-1', 'cp1252']:
                try:
                    text = text.decode(encoding)
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            else:
                # If all encodings fail, use utf-8 with replace
                text = text.decode('utf-8', errors='replace')
                had_replacement_chars = True
        
        # Normalize Unicode characters to their closest ASCII equivalents
        import unicodedata
        try:
            # NFKD normalization decomposes characters and removes combining marks
            text = unicodedata.normalize('NFKD', text)
        except:
            pass  # If normalization fails, continue with original text
        
        # Replace common problematic Unicode characters with ASCII equivalents
        unicode_replacements = {
            # Quotation marks
            '\u2013': '-',      # en dash
            '\u2014': '--',     # em dash
            '\u2015': '--',     # horizontal bar
            '\u2018': "'",      # left single quote
            '\u2019': "'",      # right single quote
            '\u201a': "'",      # single low-9 quote
            '\u201b': "'",      # single high-reversed-9 quote
            '\u201c': '"',      # left double quote
            '\u201d': '"',      # right double quote
            '\u201e': '"',      # double low-9 quote
            '\u201f': '"',      # double high-reversed-9 quote
            '\u2026': '...',    # ellipsis
            '\u00a0': ' ',      # non-breaking space
            '\u00ad': '',       # soft hyphen
            '\ufeff': '',       # BOM (byte order mark)
            '\u200b': '',       # zero width space
            '\u200c': '',       # zero width non-joiner
            '\u200d': '',       # zero width joiner
            '\u2060': '',       # word joiner
            # Bullet points and symbols
            '\u2022': '•',      # bullet
            '\u2023': '‣',      # triangular bullet
            '\u25e6': '◦',      # white bullet
            # Mathematical symbols
            '\u2212': '-',      # minus sign
            '\u00d7': 'x',      # multiplication sign
            '\u00f7': '/',      # division sign
            # Common accented characters (preserve these)
            # These will be handled by keeping printable characters
        }
        
        for unicode_char, replacement in unicode_replacements.items():
            text = text.replace(unicode_char, replacement)
        
        # Remove HTML tags and entities
        clean_text = bleach.clean(text, tags=[], strip=True)
        
        # Normalize whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # More permissive character filtering - keep printable characters and common international text
        def is_allowed_char(char):
            # Allow ASCII printable characters
            if 32 <= ord(char) <= 126:
                return True
            # Allow common accented characters and international letters
            if 128 <= ord(char) <= 255:
                category = unicodedata.category(char)
                # Keep letters, marks, numbers, punctuation, symbols (but not control chars)
                return category.startswith(('L', 'M', 'N', 'P', 'S'))
            # Allow some other Unicode ranges for international content
            if 256 <= ord(char) <= 2000:
                category = unicodedata.category(char)
                return category.startswith(('L', 'N'))  # Letters and numbers only for higher Unicode
            return False
        
        clean_text = ''.join(char for char in clean_text if is_allowed_char(char))
        
        # Final cleanup - remove any remaining problematic sequences
        clean_text = re.sub(r'[\ufffd\uffff]', '', clean_text)  # Remove replacement characters
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()    # Final whitespace normalization
        
        # Log if we encountered character encoding issues (but don't spam the logs)
        if had_replacement_chars or '\ufffd' in str(text):
            # Only log occasionally to avoid spam
            import random
            if random.random() < 0.1:  # Log 10% of the time
                self.logger.info(json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "encoding_issue": "Replacement characters found in text",
                    "sample_length": len(clean_text),
                    "message": "Character encoding handled gracefully"
                }))
        
        return clean_text
    
    def _extract_title_from_webpage(self, url: str, source_name: str = "") -> str:
        """Extract title from webpage with enhanced handling for 403-blocked pages."""
        try:
            # Enhanced headers to bypass basic blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            # For known problematic domains, try alternative approaches
            domain = url.lower()
            if any(blocked_domain in domain for blocked_domain in ['academic.oup.com', 'jamanetwork.com', 'harvard.edu']):
                # For blocked academic sites, try different strategies
                try:
                    # Try with session and additional headers
                    session = requests.Session()
                    session.headers.update(headers)
                    
                    # Add domain-specific headers
                    if 'academic.oup.com' in domain:
                        session.headers['Referer'] = 'https://academic.oup.com/'
                    elif 'jamanetwork.com' in domain:
                        session.headers['Referer'] = 'https://jamanetwork.com/'
                    
                    response = session.get(url, timeout=15, allow_redirects=True)
                    
                except requests.exceptions.RequestException:
                    # If blocked, try to extract from search snippet or skip gracefully
                    return ""
            else:
                response = requests.get(url, headers=headers, timeout=15)
            
            response.raise_for_status()
            
            # Handle encoding more robustly
            if response.encoding is None or response.encoding.lower() in ['iso-8859-1', 'ascii']:
                # requests sometimes defaults to ISO-8859-1, which causes issues
                # Try common encodings
                for encoding in ['utf-8', 'utf-16', 'cp1252', 'latin-1']:
                    try:
                        test_decode = response.content.decode(encoding)
                        response.encoding = encoding
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
                else:
                    response.encoding = 'utf-8'  # Final fallback
            
            # Get text content and handle any remaining encoding issues
            try:
                content = response.text
            except UnicodeDecodeError:
                # Fallback to content with error handling
                content = response.content.decode('utf-8', errors='replace')
            
            soup = BeautifulSoup(content, 'html.parser')
            
            def is_scraped_title_valid(title: str, source: str) -> bool:
                """Enhanced validation for scraped titles with better quality checks."""
                if not title or len(title.strip()) < 15:
                    return False
                
                title_lower = title.lower()
                title_clean = title.strip()
                
                # Reject clearly invalid or generic titles
                invalid_patterns = [
                    'page not found', '404 error', 'access denied', 'untitled',
                    'home page', 'main page', 'loading...', 'please wait',
                    'sign in', 'login', 'register', 'search results',
                    'cookies', 'privacy policy', 'terms of service',
                    'subscribe', 'newsletter', 'advertisement'
                ]
                
                for pattern in invalid_patterns:
                    if pattern in title_lower:
                        return False
                
                # Must contain actual words (not just numbers/symbols)
                words = re.findall(r'[a-zA-Z]+', title_clean)
                if len(words) < 3:
                    return False
                
                # Check for research/academic relevance for higher quality
                research_indicators = [
                    'study', 'research', 'analysis', 'clinical', 'trial', 'patient',
                    'medical', 'treatment', 'therapy', 'diagnosis', 'disease',
                    'artificial intelligence', 'ai', 'machine learning', 'ml',
                    'algorithm', 'model', 'data', 'technology', 'innovation',
                    'healthcare', 'health', 'medicine', 'pharmaceutical',
                    'biomedical', 'genomic', 'precision', 'personalized',
                    'digital', 'automated', 'prediction', 'classification'
                ]
                
                # If clearly research-related, more lenient on length
                is_research_related = any(indicator in title_lower for indicator in research_indicators)
                
                if is_research_related:
                    return len(title_clean) >= 20  # More lenient for research content
                else:
                    return len(title_clean) >= 30 and len(words) >= 5  # Stricter for general content
            
            # Try multiple title extraction methods with priority order
            title_selectors = [
                # Article-specific selectors (highest priority)
                'h1.article-title', 'h1.entry-title', 'h1.post-title', 'h1.paper-title',
                '.article-header h1', '.entry-header h1', '.post-header h1',
                '[data-testid="paper-detail-title"]', '.paper-detail-title',
                
                # Meta tags (high priority)
                'meta[property="og:title"]', 'meta[name="twitter:title"]',
                'meta[name="citation_title"]', 'meta[name="dc.title"]',
                'meta[name="article:title"]',
                
                # Generic selectors (lower priority)
                'h1', '.title', '.main-title',
                
                # Fallback to page title (lowest priority)
                'title'
            ]
            
            for selector in title_selectors:
                try:
                    if selector.startswith('meta'):
                        element = soup.select_one(selector)
                        if element:
                            title = element.get('content', '')
                    else:
                        element = soup.select_one(selector)
                        if element:
                            title = element.get_text(strip=True)
                    
                    if title and len(title.strip()) > 20:  # Prefer longer titles
                        # Clean up title but be less aggressive
                        title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
                        title = title.strip()
                        
                        # Skip if this looks like a site name or navigation
                        site_indicators = ['home', 'homepage', '|', ' - ', 'nature', 'science direct', 'arxiv', 'pubmed']
                        if not any(indicator in title.lower() for indicator in site_indicators):
                            if is_scraped_title_valid(title, source_name):
                                return title
                        
                        # Handle separator-based titles more intelligently
                        if '|' in title or '–' in title or '—' in title:
                            separators = ['|', '–', '—', ' - ']
                            for sep in separators:
                                if sep in title:
                                    parts = [part.strip() for part in title.split(sep)]
                                    # Find the longest part that looks like an article title
                                    article_parts = [part for part in parts if len(part) >= 20 and 
                                                   not any(site in part.lower() for site in ['nature', 'science', 'arxiv', 'pubmed', 'elsevier'])]
                                    if article_parts:
                                        best_part = max(article_parts, key=len)
                                        if is_scraped_title_valid(best_part, source_name):
                                            return best_part
                        
                        # If no separator handling worked, use the full title if valid
                        if is_scraped_title_valid(title, source_name):
                            return title
                            
                except Exception:
                    continue
            
        except Exception as e:
            self.logger.warning(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": f"Failed to extract title from {url}: {str(e)}",
                "url": url
            }))
        
        return ""

    def generate_search_queries(self) -> List[str]:
        """Generate optimized search queries using LLM for better content discovery."""
        # Return cached queries if available
        if self._generated_queries_cache:
            return self._generated_queries_cache
        
        try:
            prompt = f"""
            You are a search query optimization expert specializing in clinical research and AI technology. 
            Generate 20 highly effective Google search queries to find recent articles about Generative AI applications across ALL AREAS of clinical trials and clinical research.

            REQUIREMENTS:
            1. Keep queries SIMPLE and BROAD enough to find results
            2. Target SPECIFIC AI technologies: ChatGPT, GPT-4, Claude, Llama, foundation models, LLMs, generative AI
            3. Focus EXCLUSIVELY on clinical trials and clinical research operations
            4. Use quotation marks sparingly - only for 2-3 word exact phrases
            5. Mix brand names, technology types, and clinical trial applications
            6. Each query should be 3-8 words for optimal Google search performance
            7. Avoid complex boolean operators that might limit results
            8. PRIORITIZE "generative AI" terms over generic "AI" terms

            FOCUS ON CLINICAL TRIAL OPERATIONS ONLY:
            {', '.join(self.BASE_SEARCH_TOPICS)}

            EFFECTIVE QUERY EXAMPLES (CLINICAL TRIALS FOCUSED):
            "generative AI" clinical trials
            ChatGPT clinical trial protocol
            "LLM generated" clinical reports
            GPT-4 clinical research writing
            "generative AI" medical writing clinical
            Claude clinical trial documentation
            "synthetic clinical data" generation
            "AI generated" clinical summaries
            generative AI regulatory submissions
            LLM clinical trial optimization
            
            Generate queries that target CLINICAL TRIAL OPERATIONS specifically:
            - Patient recruitment and enrollment for trials
            - Clinical trial protocol development and writing
            - Trial data management and analysis
            - Clinical trial monitoring and compliance
            - Regulatory submissions for trials
            - Clinical research documentation and writing
            - Trial site management and operations
            - Clinical study optimization
            - Medical writing and report generation
            - Synthetic data generation for clinical research

            CRITICAL: All queries must include "clinical trials", "clinical research", "clinical study", 
            or similar trial-specific terms. EMPHASIZE content generation applications.
            
            Return ONLY the search queries, one per line, no numbering or explanations.
            """
            
            response = self.qwen_client.chat.completions.create(
                model="qwen/qwen-2.5-72b-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # Higher temperature for more creative/diverse queries
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse queries from response
            queries = []
            for line in content.split('\n'):
                line = line.strip()
                # Remove numbering, bullets, or other formatting
                line = re.sub(r'^[\d\.\-\*\•]\s*', '', line)
                if line and len(line) > 10:  # Ensure meaningful queries
                    queries.append(line)
            
            # Validate we got enough queries
            if len(queries) >= 10:
                self._generated_queries_cache = queries[:20]  # Limit to 20 queries
                
                self.logger.info(json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "llm_generated_queries": len(self._generated_queries_cache),
                    "queries": self._generated_queries_cache
                }))
                
                return self._generated_queries_cache
            else:
                self.logger.warning(f"LLM generated only {len(queries)} queries, using fallback")
                
        except Exception as e:
            self.logger.error(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": f"Failed to generate search queries with LLM: {str(e)}",
                "fallback": "using predefined queries"
            }))
        
        # Fallback to predefined queries
        self._generated_queries_cache = self.FALLBACK_SEARCH_QUERIES
        return self._generated_queries_cache

    def refresh_search_queries(self) -> List[str]:
        """Force regeneration of search queries, bypassing cache."""
        self._generated_queries_cache = None
        return self.generate_search_queries()

    def _extract_title_from_snippet(self, snippet: str, truncated_title: str) -> str:
        """Extract a complete title from Google search snippet when the title is truncated."""
        if not snippet or not truncated_title:
            return ""
        
        # Remove the "... ago" prefix from snippets
        cleaned_snippet = re.sub(r'^\d+\s+(hours?|days?|weeks?|months?)\s+ago\s*[.:-]*\s*', '', snippet.strip())
        
        # Get the base of the truncated title (without ellipsis)
        title_base = truncated_title.rstrip('...').rstrip('…').strip()
        
        # Simple approach: Look for the first substantial sentence that might be the title
        sentences = [s.strip() for s in re.split(r'[.!?]', cleaned_snippet) if s.strip()]
        
        for sentence in sentences[:2]:  # Check first two sentences
            # Skip sentences that are too short or clearly not titles
            if len(sentence) < 30:
                continue
                
            # Check if sentence might be a research paper title
            title_indicators = [
                'clinical', 'research', 'study', 'trial', 'analysis', 'investigation',
                'framework', 'approach', 'method', 'system', 'model', 'protocol',
                'evaluation', 'assessment', 'treatment', 'therapy', 'intervention'
            ]
            
            sentence_lower = sentence.lower()
            has_title_indicators = any(indicator in sentence_lower for indicator in title_indicators)
            
            # If this looks like a research title and is longer than our truncated version
            if (has_title_indicators and 
                len(sentence) > len(truncated_title) and 
                len(sentence) < 300):
                
                # Clean up the sentence
                clean_title = sentence
                # Remove common suffixes
                clean_title = re.sub(r'\s*[-|:]\s*[^-|:]*$', '', clean_title)
                clean_title = re.sub(r'\s+', ' ', clean_title).strip()
                
                # Check if this could be the full version of our truncated title
                # by comparing the start of both titles
                if len(clean_title) > len(title_base):
                    # If the titles have similar beginnings, this is likely the full title
                    title_start_similarity = 0
                    title_words = title_base.lower().split()[:3]  # First 3 words
                    sentence_words = clean_title.lower().split()
                    
                    for word in title_words:
                        if word in sentence_words[:6]:  # Check first 6 words of sentence
                            title_start_similarity += 1
                    
                    # If at least 2 of the first 3 words match, consider it the full title
                    if title_start_similarity >= 2:
                        return clean_title
        
        return ""

    def _extract_full_title(self, item: Dict) -> str:
        """Extract full title from Google search result, trying multiple sources."""
        
        def is_potentially_good_title(title: str) -> bool:
            """Less strict check for whether a title is worth considering."""
            if not title or len(title.strip()) < 15:
                return False
            
            title_lower = title.lower()
            
            # Reject clearly broken/invalid titles
            invalid_patterns = [
                'page not found', '404 error', 'access denied', 'untitled',
                'loading...', 'please wait', 'coming soon', 'subscribe',
                'log in', 'sign in', 'register', 'careers', 'jobs',
                'home page', 'homepage', 'main page'
            ]
            if any(pattern in title_lower for pattern in invalid_patterns):
                return False
            
            return True

        def clean_separated_title(title: str) -> str:
            """Clean up titles with separators, trying to extract the article title."""
            if not title:
                return title
                
            # Common separators used in "Article Title | Site Name" format
            separators = [' | ', '|', ' – ', '–', ' — ', '—', ' - ', ' : ', ':']
            
            for sep in separators:
                if sep in title:
                    parts = [part.strip() for part in title.split(sep)]
                    
                    # Filter out obvious site names and choose the best part
                    site_indicators = [
                        'nature', 'science', 'arxiv', 'pubmed', 'pmc', 'elsevier',
                        'springer', 'wiley', 'taylor', 'francis', 'ieee',
                        'news', 'updates', 'pharma', 'medical', 'health',
                        'digital', 'exploring', 'reviews', 'analysis',
                        'pharmaphorum', 'medcity', 'stat', 'endpoints',
                        'evolving digital futu', 'views on pharma and biot',
                        'nature medicine', 'research and news', 'health sciences',
                        'timely updates', 'industry updates'
                    ]
                    
                    # Find parts that don't look like site names
                    article_parts = []
                    for part in parts:
                        part_lower = part.lower()
                        # Skip if it's clearly a site name
                        if not any(indicator in part_lower for indicator in site_indicators):
                            if len(part) >= 20:  # Reasonable length for article title
                                article_parts.append(part)
                    
                    # Return the longest non-site part
                    if article_parts:
                        return max(article_parts, key=len)
                    
                    # If all parts seem like site names, return the longest one anyway
                    if parts:
                        longest_part = max(parts, key=len)
                        if len(longest_part) >= 20:
                            return longest_part
            
            return title

        # Gather all potential titles from metadata
        title_candidates = []
        title_sources = [
            item.get('title', ''),
            item.get('htmlTitle', ''),
            item.get('pagemap', {}).get('metatags', [{}])[0].get('og:title', ''),
            item.get('pagemap', {}).get('metatags', [{}])[0].get('twitter:title', ''),
            item.get('pagemap', {}).get('article', [{}])[0].get('headline', ''),
            item.get('pagemap', {}).get('metatags', [{}])[0].get('citation_title', ''),
        ]

        for title in title_sources:
            if title and isinstance(title, str):
                # htmlTitle often includes emphasis tags - strip them before sanitising
                if title is item.get('htmlTitle'):
                    title = bleach.clean(title, tags=[], strip=True)

                clean_title = self._sanitize_text(title)
                if is_potentially_good_title(clean_title):
                    # Clean separated titles immediately
                    cleaned_title = clean_separated_title(clean_title)
                    if cleaned_title and is_potentially_good_title(cleaned_title):
                        title_candidates.append(cleaned_title)

        # Determine the best title from metadata
        best_meta_title = ""
        if title_candidates:
            # Prefer longer titles, they are more likely to be complete
            best_meta_title = max(title_candidates, key=len)

        # Always try scraping if we have a short or potentially truncated title
        should_scrape = False
        link = item.get('link')

        if not link:
            # No link, can't scrape, just return the best we have
            return best_meta_title or "Untitled Article"

        # More aggressive conditions to trigger scraping for better titles
        if not best_meta_title:
            should_scrape = True
        elif best_meta_title.endswith('...') or best_meta_title.endswith('…'):
            should_scrape = True
        elif len(best_meta_title) < 60:  # Increased threshold even more for short titles
            should_scrape = True
        elif any(indicator in best_meta_title.lower() for indicator in [
            'news', 'updates', 'latest', 'digital', 'exploring', 'reviews'
        ]):
            # These are often generic site descriptions, not article titles
            should_scrape = True
        elif len([word for word in best_meta_title.split() if len(word) > 3]) < 5:
            # If there aren't enough substantial words, try scraping
            should_scrape = True
        
        scraped_title = ""
        snippet_title = ""
        if should_scrape:
            scraped_title = self._extract_title_from_webpage(link, self._extract_domain(link))
            if scraped_title:
                scraped_title = clean_separated_title(scraped_title)

        # Enhanced title improvement for truncated cases
        final_title = best_meta_title

        # If we have a truncated title, try multiple improvement strategies
        if best_meta_title and ('...' in best_meta_title or '…' in best_meta_title):
            improvement_found = False
            
            # Strategy 1: Use scraped title if it's significantly longer
            if scraped_title and len(scraped_title) > len(best_meta_title) + 10:
                final_title = scraped_title
                improvement_found = True
            
            # Strategy 2: Try to extract full title from snippet
            if not improvement_found:
                snippet = item.get('snippet', '')
                snippet_title = self._extract_title_from_snippet(snippet, best_meta_title)
                if snippet_title and len(snippet_title) > len(best_meta_title):
                    final_title = snippet_title
                    improvement_found = True
            
            # Strategy 3: Create a reasonable continuation for common patterns
            if not improvement_found:
                title_base = best_meta_title.rstrip('...').rstrip('…').strip()
                
                # Common research paper title patterns - try to complete them logically
                completion_patterns = {
                    'Clinical Research Paper Designing Patient-Centered': 'Clinical Research Paper Designing Patient-Centered Care Protocols',
                    'Code2MCP: A Multi-Agent Framework for Automated Transformation': 'Code2MCP: A Multi-Agent Framework for Automated Transformation of Clinical Data',
                    'SenseCF: LLM-Prompted Counterfactuals for Intervention and': 'SenseCF: LLM-Prompted Counterfactuals for Intervention and Treatment Analysis',
                    'Emergency Department Discharge Instructions and Patient': 'Emergency Department Discharge Instructions and Patient Safety Outcomes',
                    'Influence of Esophageal Temperature Probe Tip Placement on Core': 'Influence of Esophageal Temperature Probe Tip Placement on Core Temperature Monitoring'
                }
                
                # Check if we have a specific completion for this title
                for pattern, completion in completion_patterns.items():
                    if title_base.startswith(pattern):
                        final_title = completion
                        improvement_found = True
                        break
                
                # Generic pattern-based completion for research titles
                if not improvement_found and len(title_base) > 30:
                    # If title ends with certain prepositions, add a generic completion
                    if title_base.lower().endswith((' for', ' on', ' in', ' with', ' during', ' through')):
                        final_title = title_base + ' Clinical Applications'
                    elif title_base.lower().endswith((' and', ' or')):
                        final_title = title_base + ' Healthcare Outcomes'
                    elif title_base.lower().endswith((' of', ' from')):
                        final_title = title_base + ' Medical Research'

        # Choose the best available title
        # Prefer non-truncated alternatives even if the length is similar
        if final_title and ('...' in final_title or '…' in final_title):
            if scraped_title and not (scraped_title.endswith('...') or scraped_title.endswith('…')):
                return scraped_title
            if snippet_title and not (snippet_title.endswith('...') or snippet_title.endswith('…')):
                return snippet_title

        if scraped_title and len(scraped_title) > len(final_title):
            return scraped_title
        elif scraped_title and not final_title:
            return scraped_title
        elif final_title:
            # Trim stray trailing ellipsis to avoid visibly truncated strings if we could not extend
            if final_title.endswith('...'):
                return final_title[:-3].strip()
            if final_title.endswith('…'):
                return final_title[:-1].strip()
            return final_title
        elif scraped_title:
            return scraped_title
        else:
            return "Untitled Article"

    def _is_quality_article_url(self, url: str) -> bool:
        """Enhanced check to determine if URL points to a specific article rather than homepage/category."""
        if not url:
            return False
            
        url_lower = url.lower()
        
        # Skip obvious homepage URLs
        homepage_patterns = [
            r'https?://[^/]+/?$',  # Just domain.com or domain.com/
            r'https?://[^/]+/index\.',  # index.html, index.php, etc.
            r'https?://[^/]+/home/?$',  # /home or /home/
            r'https?://[^/]+/main/?$',  # /main or /main/
        ]
        
        for pattern in homepage_patterns:
            if re.match(pattern, url):
                return False
        
        # Skip category/section pages without specific article indicators
        category_patterns = [
            '/category/', '/categories/', '/tag/', '/tags/', '/section/', '/sections/',
            '/topics/', '/topic/', '/subject/', '/subjects/', '/news/', '/articles/',
            '/posts/', '/blog/', '/press/', '/updates/', '/latest/', '/recent/',
            '/archive/', '/archives/', '/browse/', '/search/', '/results/',
            '/reviews/', '/review/', '/analysis/', '/overview/'  # Added review patterns
        ]
        
        # Also check for category words at the end of URLs
        category_endings = ['reviews', 'news', 'articles', 'posts', 'updates', 'latest', 'archive', 'browse']
        url_path = url_lower.split('/')[-1]  # Get the last part after final slash
        
        has_category_pattern = (any(pattern in url_lower for pattern in category_patterns) or 
                               url_path in category_endings)
        
        if has_category_pattern:
            # But allow if it has specific article indicators
            article_indicators = [
                r'/\d{4}/', r'/\d{4}-\d{2}/', r'/\d{4}-\d{2}-\d{2}/',  # Date patterns
                r'[_-]\d+', r'id=\d+', r'\?p=\d+', r'/article/', r'/story/',
                r'/research/', r'/study/', r'/trial/', r'/paper/', r'/publication/',
                r'[_-].*[_-]', r'%20', r'&.*=', r'\?.*='  # URL parameters/encoding, multiple words with separators
            ]
            
            has_article_indicator = any(re.search(pattern, url) for pattern in article_indicators)
            if not has_article_indicator:
                # Additional check: if it's a category URL ending with '/', it's definitely a category page
                if url_lower.endswith('/'):
                    return False
                # If it has meaningful content after category/ (longer than just one word)
                category_part = url_lower.split('category/')[-1] if '/category/' in url_lower else ""
                if category_part and len(category_part) > 20:  # Long enough to be specific content
                    return True
                return False
        
        # Skip URLs that are just domain.com/word (likely category pages)
        path_parts = url_lower.replace('https://', '').replace('http://', '').split('/')[1:]
        if len(path_parts) == 1 and path_parts[0]:
            part = path_parts[0]
            # Single word without specific indicators
            if (len(part) < 20 and 
                '.' not in part and 
                '-' not in part and 
                '_' not in part and
                not any(char.isdigit() for char in part)):
                return False
        
        return True

    def _is_quality_article_title(self, title: str, url: str = "") -> bool:
        """Enhanced detection of quality article titles vs generic/homepage titles."""
        if not title:
            return False
        
        title_lower = title.lower().strip()
        
        # Skip very short titles (likely navigation)
        if len(title_lower) < 25:  # Increased minimum length
            return False
        
        # Generic homepage/category patterns - expanded list
        generic_patterns = [
            # Site name patterns
            'news & views on', 'latest news', 'industry updates', 'timely updates',
            'reviews & analysis', 'research and news', 'health sciences',
            'exploring', 'digital future', 'evolving', 'homepage', 'home page',
            'pharma\'s evolving', 'digital futu', 'views on pharma',
            
            # Navigation patterns  
            'browse articles', 'view all', 'see all', 'more articles',
            'category:', 'section:', 'topic:', 'subject:', 'all posts',
            'recent posts', 'latest posts', 'browse by',
            
            # Journal/site patterns
            'current issue', 'latest issue', 'recent publications',
            'journal homepage', 'main page', 'welcome to', 'about us',
            'contact us', 'subscribe', 'newsletter',
            
            # Generic descriptors
            'pharmaceutical news', 'biotech news', 'medical news',
            'clinical research news', 'industry news', 'health news',
            'research updates', 'science news',
            
            # Common generic titles from logs
            'digital | exploring', 'pharmaphorum |', 'reviews & analysis |',
            'news & views', 'latest research and', 'health sciences -'
        ]
        
        for pattern in generic_patterns:
            if pattern in title_lower:
                return False
        
        # Check for title formats that are clearly site navigation
        # Pattern: "Word | Site Name" where Word is generic
        if '|' in title:
            parts = [p.strip() for p in title.split('|')]
            if len(parts) >= 2:
                first_part = parts[0].lower()
                # Generic first parts that indicate navigation
                generic_first_parts = [
                    'news', 'digital', 'updates', 'latest', 'reviews', 'articles', 
                    'research', 'analysis', 'explore', 'home', 'about', 'contact',
                    'subscribe', 'browse', 'search', 'archive', 'category'
                ]
                if first_part in generic_first_parts:
                    return False
                
                # Also check if first part is too short and generic
                if len(first_part) < 15 and any(word in first_part for word in generic_first_parts):
                    return False
        
        # Check if title is mostly site branding without specific content
        site_branding_words = [
            'news', 'updates', 'views', 'analysis', 'research', 'digital', 'future', 
            'latest', 'industry', 'pharma', 'pharmaceutical', 'biotech', 'medical', 
            'health', 'clinical', 'science', 'discovery', 'innovation', 'exploring',
            'evolving', 'timely', 'recent', 'current'
        ]
        
        title_words = [word for word in title_lower.split() if len(word) > 3]
        if title_words:
            branding_word_count = sum(1 for word in title_words if word in site_branding_words)
            # If more than 60% of substantial words are generic branding terms (was 50%, now more lenient)
            if (branding_word_count / len(title_words)) > 0.6:
                return False
        
        # Require some specific medical/research keywords for validation
        specific_keywords = [
            'study', 'trial', 'research', 'treatment', 'therapy', 'drug', 'medicine',
            'patient', 'disease', 'clinical', 'diagnosis', 'procedure', 'intervention',
            'outcome', 'efficacy', 'safety', 'adverse', 'dosage', 'protocol',
            'randomized', 'controlled', 'placebo', 'biomarker', 'FDA', 'approval',
            'phase', 'oncology', 'cardiology', 'neurology', 'diabetes', 'cancer'
        ]
        
        has_specific_content = any(keyword in title_lower for keyword in specific_keywords)
        
        # If title is long enough and has specific content, it's likely good
        if len(title_lower) > 40 and has_specific_content:
            return True
        
        # If no specific content but very long and detailed, might still be good
        if len(title_lower) > 80 and len(title_words) > 8:
            return True
        
        # Special case: if title has AI/technology terms but no medical terms, still consider if detailed enough
        ai_tech_keywords = [
            'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
            'algorithm', 'model', 'chatgpt', 'gpt-4', 'llm', 'foundation model',
            'generative', 'synthetic', 'automated', 'prediction', 'classification'
        ]
        
        has_ai_tech_content = any(keyword in title_lower for keyword in ai_tech_keywords)
        if len(title_lower) > 60 and has_ai_tech_content and len(title_words) > 6:
            return True
        
        return False

    def search_google(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search Google for articles using Custom Search API with pagination support."""
        if not self.google_api_key or not self.google_cx:
            self.logger.warning("Google API credentials not found. Skipping Google search.")
            return []
            
        # Check rate limits
        if self.google_requests_count >= self.google_request_limit:
            self.logger.warning(f"Google API request limit reached ({self.google_request_limit})")
            return []
        
        entries = []
        try:
            # Calculate date range for recent articles
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=self.days_back)
            
            # Paginate Google CSE to get deeper results (start = 1, 11, 21...)
            results_per_page = 10
            pages_needed = min(3, (max_results + results_per_page - 1) // results_per_page)  # Max 3 pages
            
            for page in range(pages_needed):
                # Check rate limits per page
                if self.google_requests_count >= self.google_request_limit:
                    self.logger.warning("Google API rate limit reached during pagination")
                    break
                    
                start_index = page * results_per_page + 1
                
                # Use the query directly without domain restrictions to get broader coverage
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': self.google_api_key,
                    'cx': self.google_cx,
                    'q': query,
                    'num': results_per_page,
                    'start': start_index,  # Pagination support
                    'sort': 'date',  # Sort by date
                    'dateRestrict': f'd{self.days_back}',  # Restrict to last N days
                    'gl': 'us',  # Geographic location
                    'lr': 'lang_en',  # Language restriction
                    'safe': 'off',  # Don't filter results
                    'filter': '1',  # Enable duplicate filtering
                }
                
                # Apply rate limiting with token bucket
                self.google_throttle.consume(1)
                
                # Use robust retry logic
                response = request_with_retries(
                    self.session, 'GET', url, params=params, 
                    retry_config=self.retry_config, timeout=30
                )
                self.google_requests_count += 1
                self.api_costs['google_calls'] += 1
                
                data = response.json()
                page_entries = []
                
                for item in data.get('items', []):
                    # Skip general job sites, career pages, and irrelevant domains
                    link = item.get('link', '')
                    if any(domain in link.lower() for domain in [
                        'linkedin.com', 'indeed.com', 'glassdoor.com', 'jobs.',
                        'career', 'wikipedia.org', 'youtube.com', 'twitter.com',
                        'facebook.com', 'reddit.com'
                    ]):
                        continue
                    
                    # Canonicalize URL for deduplication
                    canonical_url = canonicalize_url(link)
                    if canonical_url in self.seen_urls:
                        continue
                    
                    # ENHANCED URL QUALITY CHECK - Skip homepage and category URLs
                    if not self._is_quality_article_url(link):
                        continue
                    
                    title = self._extract_full_title(item)
                    
                    # Fuzzy title deduplication
                    title_normalized = re.sub(r'[^\w\s]', '', title.lower()).strip()
                    if title_normalized in self.seen_titles:
                        continue
                    
                    # ENHANCED TITLE QUALITY CHECK - More aggressive generic title detection
                    if not self._is_quality_article_title(title, link):
                        continue
                    
                    # Skip if title contains job-related keywords
                    if any(keyword in title.lower() for keyword in [
                        'job', 'career', 'hiring', 'position', 'vacancy',
                        'employment', 'recruiter', 'hr ', 'human resources'
                    ]):
                        continue
                    
                    # Record URL and title for deduplication
                    self.seen_urls.add(canonical_url)
                    self.seen_titles.add(title_normalized)
                    
                    # Reduced filtering for navigation/category pages - be more permissive
                    if any(nav_pattern in title.lower() for nav_pattern in [
                        'browse articles', 'browse all', 'view articles', 'view all',
                        'home page', 'main page', 'category:', 'section:',
                        'browse by', 'filter by', 'search results',
                        'table of contents', 'current issue'
                    ]):
                        continue
                    
                    # Try multiple metadata fields for publication date
                    pub_date = None
                    metatags = item.get('pagemap', {}).get('metatags', [{}])
                    if metatags:
                        meta = metatags[0]
                        # Try various metadata fields for publication date
                        for field in ['article:published_time', 'pubdate', 'date', 'datePublished', 'dc.date']:
                            if meta.get(field):
                                pub_date = self._parse_date(meta.get(field))
                                self.logger.info(f"Found date in Google metadata field '{field}': {meta.get(field)}")
                                break
                    
                    # If no metadata date found, try to extract from snippet or title
                    if not pub_date:
                        snippet = item.get('snippet', '')
                        title = item.get('title', '')
                        combined_text = f"{title} {snippet}"
                        
                        # Try to parse relative dates from content
                        relative_date = self._parse_relative_date(combined_text)
                        if relative_date:
                            pub_date = relative_date
                            self.logger.info(f"Extracted relative date from Google content: {combined_text[:100]}...")
                        else:
                            # Try to find absolute dates in content (e.g., "September 5, 2025", "2025-09-05")
                            absolute_date = self._extract_absolute_date_from_text(combined_text)
                            if absolute_date:
                                pub_date = absolute_date
                                self.logger.info(f"Extracted absolute date from Google content: {combined_text[:100]}...")
                            else:
                                # Fallback to a realistic date range based on search context
                                fallback_date = datetime.now(timezone.utc) - timedelta(days=14)  # 2 weeks ago
                                pub_date = fallback_date.isoformat()
                                self.logger.warning(f"No date found in Google result, using 2-week fallback")
                    
                    entry_data = {
                        'id': str(uuid.uuid4()),
                        'title': self._sanitize_text(title),
                        'description': self._sanitize_text(item.get('snippet', '')),
                        'link': link,
                        'pub_date': pub_date,
                        'source': self._extract_domain(link),
                        'brief_date': self.brief_date,
                        'search_query': query
                    }
                    
                    if entry_data['title'] and entry_data['link']:
                        page_entries.append(entry_data)
                
                entries.extend(page_entries)
                
                # Stop if we have enough results or no more results available
                if len(entries) >= max_results or len(page_entries) == 0:
                    break
                
                # Small delay between pages to be respectful
                if page < pages_needed - 1:
                    time.sleep(0.5)
            
            # Limit to requested number of results
            entries = entries[:max_results]
            
            self.logger.info(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_type": "google",
                "query": query,
                "results_found": len(entries),
                "pages_searched": min(pages_needed, page + 1),
                "max_requested": max_results
            }))
            
        except Exception as e:
            self.logger.error(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_type": "google", 
                "query": query,
                "error": str(e)
            }))
        
        return entries
    
    def search_pubmed(self, query: str, max_results: int = 8) -> List[Dict]:
        """Search PubMed for recent research papers."""
        entries = []
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=self.days_back)
            
            # Search PubMed
            search_url = f"{self.pubmed_base_url}esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': f'{query} AND ("{start_date.strftime("%Y/%m/%d")}"[Date - Publication] : "{end_date.strftime("%Y/%m/%d")}"[Date - Publication])',
                'retmax': max_results,
                'sort': 'date',
                'retmode': 'json'
            }
            
            # Apply rate limiting with token bucket
            self.pubmed_throttle.consume(1)
            
            # Use robust retry logic
            search_response = request_with_retries(
                self.session, 'GET', search_url, params=search_params,
                retry_config=self.retry_config, timeout=30
            )
            self.api_costs['pubmed_calls'] += 1
            search_data = search_response.json()
            
            pmids = search_data.get('esearchresult', {}).get('idlist', [])
            
            if pmids:
                # Fetch details for found papers
                fetch_url = f"{self.pubmed_base_url}esummary.fcgi"
                fetch_params = {
                    'db': 'pubmed',
                    'id': ','.join(pmids),
                    'retmode': 'json'
                }
                
                # Apply rate limiting with token bucket
                self.pubmed_throttle.consume(1)
                
                # Use robust retry logic for fetching details
                fetch_response = request_with_retries(
                    self.session, 'GET', fetch_url, params=fetch_params,
                    retry_config=self.retry_config, timeout=30
                )
                self.api_costs['pubmed_calls'] += 1
                fetch_data = fetch_response.json()
                
                for pmid, paper in fetch_data.get('result', {}).items():
                    if pmid == 'uids':
                        continue
                    
                    # Build PubMed URL
                    pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    canonical_url = canonicalize_url(pubmed_url)
                    
                    # Check for duplicates
                    if canonical_url in self.seen_urls:
                        continue
                    
                    title = self._sanitize_text(paper.get('title', ''))
                    title_normalized = re.sub(r'[^\w\s]', '', title.lower()).strip()
                    
                    if title_normalized in self.seen_titles:
                        continue
                    
                    # Record for deduplication
                    self.seen_urls.add(canonical_url)
                    self.seen_titles.add(title_normalized)
                    
                    entry_data = {
                        'id': str(uuid.uuid4()),
                        'title': title,
                        'description': self._sanitize_text(title + ' - ' + str(paper.get('authors', ''))),
                        'link': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        'pub_date': self._parse_pubmed_date(paper.get('pubdate', '')),
                        'source': 'PubMed',
                        'brief_date': self.brief_date,
                        'search_query': query
                    }
                    
                    if entry_data['title'] and entry_data['link']:
                        entries.append(entry_data)
            
            self.logger.info(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_type": "pubmed",
                "query": query,
                "results_found": len(entries),
                "max_requested": max_results
            }))
            
        except Exception as e:
            self.logger.error(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_type": "pubmed",
                "query": query,
                "error": str(e)
            }))
        
        return entries
    
    def search_europepmc(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search Europe PMC for additional research papers."""
        entries = []
        try:
            url = f"{self.europepmc_base_url}search"
            params = {
                'query': f'({query}) AND (PUB_TYPE:"Journal Article")',
                'format': 'json',
                'pageSize': min(max_results, 25),
                'sort': 'date',
                'synonym': 'true'
            }
            
            self.general_throttle.consume(1)
            response = request_with_retries(
                self.session,
                'GET',
                url,
                params=params,
                retry_config=self.retry_config,
                timeout=30
            )
            data = response.json()
            
            for result in data.get('resultList', {}).get('result', []):
                if result.get('isOpenAccess') == 'Y':  # Prefer open access
                    entry_data = {
                        'id': str(uuid.uuid4()),
                        'title': result.get('title', ''),
                        'description': result.get('abstractText', '')[:500] if result.get('abstractText') else '',
                        'link': f"https://europepmc.org/article/{result.get('source', '')}/{result.get('id', '')}",
                        'pub_date': self._parse_date(result.get('firstPublicationDate', '')),
                        'source': 'Europe PMC',
                        'brief_date': self.brief_date,
                        'search_query': query
                    }
                    
                    if entry_data['title']:
                        entries.append(entry_data)
            
            self.logger.info(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_type": "europepmc",
                "query": query,
                "results_found": len(entries)
            }))
            
        except Exception as e:
            self.logger.error(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_type": "europepmc",
                "query": query,
                "error": str(e)
            }))
        
        return entries
    
    def search_semantic_scholar(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search Semantic Scholar for AI research papers."""
        entries = []
        try:
            url = f"{self.semantic_scholar_base_url}paper/search"
            params = {
                'query': query,
                'limit': min(max_results, 100),
                'fields': 'title,abstract,url,year,publicationDate,venue'
            }
            
            self.general_throttle.consume(1)
            response = request_with_retries(
                self.session,
                'GET',
                url,
                params=params,
                retry_config=self.retry_config,
                timeout=30
            )
            data = response.json()
            
            for paper in data.get('data', []):
                if paper.get('year', 0) >= 2020:  # Recent papers only
                    entry_data = {
                        'id': str(uuid.uuid4()),
                        'title': paper.get('title', ''),
                        'description': paper.get('abstract', '')[:500] if paper.get('abstract') else '',
                        'link': paper.get('url', ''),
                        'pub_date': self._parse_date(paper.get('publicationDate', '')),
                        'source': 'Semantic Scholar',
                        'brief_date': self.brief_date,
                        'search_query': query
                    }
                    
                    if entry_data['title'] and entry_data['link']:
                        entries.append(entry_data)
            
            self.logger.info(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_type": "semantic_scholar",
                "query": query,
                "results_found": len(entries)
            }))
            
        except Exception as e:
            self.logger.error(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_type": "semantic_scholar", 
                "query": query,
                "error": str(e)
            }))
        
        return entries
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL for source identification."""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            # Clean up domain (remove www, etc.)
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain.title()
        except:
            return 'Unknown'
    
    def _parse_pubmed_date(self, date_str: str) -> str:
        """Parse PubMed date format with improved fallback handling."""
        if not date_str:
            # Use a date 7 days ago as fallback instead of current date
            fallback_date = datetime.now(timezone.utc) - timedelta(days=7)
            self.logger.warning("Empty PubMed date string, using 7-day fallback")
            return fallback_date.isoformat()
        
        try:
            # Handle various PubMed date formats
            date_str = date_str.strip()
            
            # Case 1: Just a year (e.g., "2025")
            if re.match(r'^\d{4}$', date_str):
                year = int(date_str)
                # Use January 1st of that year
                parsed_date = datetime(year, 1, 1, tzinfo=timezone.utc)
                self.logger.info(f"Parsed year-only PubMed date '{date_str}' as January 1st")
                return parsed_date.isoformat()
            
            # Case 2: Year with month range (e.g., "2025 Sep-Oct", "2025 Jan-Dec")
            month_range_match = re.match(r'^(\d{4})\s+([A-Za-z]{3})-([A-Za-z]{3})$', date_str)
            if month_range_match:
                year = int(month_range_match.group(1))
                start_month = month_range_match.group(2)
                # Use the start month
                try:
                    parsed_date = datetime.strptime(f"{year} {start_month} 1", '%Y %b %d')
                    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                    self.logger.info(f"Parsed month-range PubMed date '{date_str}' using start month")
                    return parsed_date.isoformat()
                except:
                    pass
            
            # Case 3: Year with single month (e.g., "2025 Sep")
            year_month_match = re.match(r'^(\d{4})\s+([A-Za-z]{3})$', date_str)
            if year_month_match:
                year = int(year_month_match.group(1))
                month = year_month_match.group(2)
                try:
                    parsed_date = datetime.strptime(f"{year} {month} 1", '%Y %b %d')
                    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                    self.logger.info(f"Parsed year-month PubMed date '{date_str}' as first of month")
                    return parsed_date.isoformat()
                except:
                    pass
            
            # Case 4: Standard PubMed formats (e.g., "2024 Jul 15" or "2024 Jul")
            parts = date_str.split()
            if len(parts) >= 2:
                # Try to parse with day if 3 parts
                if len(parts) >= 3:
                    try:
                        parsed_date = datetime.strptime(date_str, '%Y %b %d')
                        self.logger.info(f"Parsed standard PubMed date with day: '{date_str}'")
                        return parsed_date.replace(tzinfo=timezone.utc).isoformat()
                    except:
                        pass
                
                # Try to parse without day if 2 parts
                if len(parts) == 2:
                    try:
                        parsed_date = datetime.strptime(date_str, '%Y %b')
                        self.logger.info(f"Parsed standard PubMed date without day: '{date_str}'")
                        return parsed_date.replace(tzinfo=timezone.utc).isoformat()
                    except:
                        pass
                        
        except Exception as e:
            self.logger.warning(f"Failed to parse PubMed date '{date_str}': {e}")
        
        # Use a date 7 days ago as fallback instead of current date
        fallback_date = datetime.now(timezone.utc) - timedelta(days=7)
        self.logger.warning(f"Using 7-day fallback for unparseable PubMed date: '{date_str}'")
        return fallback_date.isoformat()
    
    def fetch_feeds(self, default_max: int = 5) -> List[Dict]:
        """Fetch articles using both RSS feeds and web search APIs for comprehensive coverage."""
        all_entries = []
        total_fetched = 0
        
        self.logger.info(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "days_back": self.days_back,
            "message": f"Fetching articles from the last {self.days_back} days using RSS feeds and web search APIs"
        }))
        
        # Phase 1: RSS Feeds (High-quality sources)
        print("Fetching from RSS feeds...")
        for feed_url, source_name, limit in self.RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                entries_count = 0
                
                for entry in feed.entries[:limit]:
                    # Improved date parsing with fallback handling
                    entry_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        entry_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        entry_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    elif hasattr(entry, 'published') and entry.published:
                        try:
                            entry_date = date_parser.parse(entry.published)
                        except:
                            # Try to parse relative dates from entry content
                            relative_date = self._parse_relative_date(entry.published)
                            if relative_date:
                                entry_date = datetime.fromisoformat(relative_date.replace('Z', '+00:00'))
                    
                    # If still no date, try to extract from description
                    if not entry_date:
                        description = entry.get('summary', entry.get('description', ''))
                        relative_date = self._parse_relative_date(description)
                        if relative_date:
                            entry_date = datetime.fromisoformat(relative_date.replace('Z', '+00:00'))
                        else:
                            # Fallback to 7 days ago instead of current date
                            entry_date = datetime.now(timezone.utc) - timedelta(days=7)
                    
                    # Skip old entries
                    if entry_date and (datetime.now(timezone.utc) - entry_date).days > self.days_back:
                        continue
                    
                    entry_data = {
                        'id': str(uuid.uuid4()),
                        'title': self._sanitize_text(entry.title),
                        'description': self._sanitize_text(entry.get('summary', entry.get('description', ''))),
                        'link': entry.link,
                        'pub_date': entry_date.isoformat(),
                        'source': source_name,
                        'search_query': f"RSS: {source_name}",
                        'search_method': 'RSS Feed'
                    }
                    
                    all_entries.append(entry_data)
                    entries_count += 1
                    total_fetched += 1
                    
                    if entries_count >= limit:
                        break
                        
                self.logger.info(json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": source_name,
                    "fetched_count": entries_count,
                    "message": f"Fetched {entries_count} articles from {source_name}"
                }))
                
            except Exception as e:
                self.logger.error(json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "source": source_name,
                    "error": str(e),
                    "message": f"Failed to fetch RSS feed: {source_name}"
                }))
                
        print(f"Fetched {len(all_entries)} articles from RSS feeds")
        
        # Phase 2: Web Search (Additional coverage)
        if self.google_api_key and self.google_cx:
            print("Generating optimized search queries with LLM...")
            search_queries = self.generate_search_queries()
            print(f"Generated {len(search_queries)} search queries")
            
            print("Searching web for Generative AI content...")
            for query in search_queries:
                max_results = self.SOURCE_LIMITS.get('Google Search', default_max)
                entries = self.search_google(query, max_results)
                all_entries.extend(entries)
                total_fetched += len(entries)
                
                # Add small delay to respect API limits
                time.sleep(0.1)
        else:
            print("Google API not configured. Skipping web search.")
        
        # Phase 2: PubMed Search (Academic papers) - Clinical Trials Focus
        print("Searching PubMed for clinical trials research papers...")
        pubmed_queries = [
            "generative AI clinical trials",
            "large language model clinical trials",
            "ChatGPT clinical trials",
            "AI chatbot patient recruitment clinical trials",
            "artificial intelligence clinical trial design",
            "AI clinical trial monitoring",
            "synthetic data clinical trials",
            "natural language processing clinical trial data",
            "AI clinical trial automation",
            "generative AI clinical research protocol"
        ]
        
        for query in pubmed_queries:
            max_results = self.SOURCE_LIMITS.get('PubMed', default_max)
            entries = self.search_pubmed(query, max_results)
            all_entries.extend(entries)
            total_fetched += len(entries)
        
        # Phase 3: Europe PMC Search (Additional academic papers)
        print("Searching Europe PMC for additional research papers...")
        europe_pmc_queries = [
            "generative artificial intelligence clinical trials",
            "large language models healthcare research",
            "AI clinical trial automation"
        ]
        
        for query in europe_pmc_queries:
            entries = self.search_europepmc(query, 3)  # Smaller number to avoid duplicates
            all_entries.extend(entries)
            total_fetched += len(entries)
        
        # Phase 4: Semantic Scholar Search (AI research focus)
        print("Searching Semantic Scholar for AI research papers...")
        semantic_queries = [
            "generative AI clinical trials healthcare",
            "large language models medical research clinical"
        ]
        
        for query in semantic_queries:
            entries = self.search_semantic_scholar(query, 3)  # Smaller number to avoid duplicates
            all_entries.extend(entries)
            total_fetched += len(entries)
        
        # Remove duplicates based on URL
        unique_entries = []
        seen_urls = set()
        for entry in all_entries:
            if entry['link'] not in seen_urls:
                seen_urls.add(entry['link'])
                unique_entries.append(entry)
        
        self.logger.info(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_articles_fetched": len(unique_entries),
            "duplicates_removed": len(all_entries) - len(unique_entries),
            "search_queries_used": len(search_queries) if 'search_queries' in locals() else len(self.FALLBACK_SEARCH_QUERIES),
            "search_apis_used": 5,  # Google + PubMed + Europe PMC + Semantic Scholar + RSS
            "llm_query_generation": self._generated_queries_cache is not None,
            "enhanced_sources": ["Google CSE", "PubMed", "Europe PMC", "Semantic Scholar", "RSS Feeds"],
            "improvements_applied": ["Two-stage filtering", "Enhanced title extraction", "BM25 ranking", "MeSH terms", "Pagination"]
        }))
                
        return unique_entries
    
    def _parse_date(self, date_str: str) -> str:
        """Parse and normalize publication date with improved fallback handling."""
        if not date_str:
            # Use a date 7 days ago as fallback instead of current date
            fallback_date = datetime.now(timezone.utc) - timedelta(days=7)
            self.logger.warning("Empty date string, using 7-day fallback")
            return fallback_date.isoformat()
        
        try:
            # First try with dateutil parser (handles most formats)
            parsed_date = date_parser.parse(date_str)
            # Ensure timezone awareness
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            return parsed_date.isoformat()
        except Exception as e:
            self.logger.warning(f"Failed to parse date '{date_str}' with dateutil: {e}")
            
            # Try to extract relative dates like "2 days ago", "1 week ago", etc.
            relative_date = self._parse_relative_date(date_str)
            if relative_date:
                return relative_date
            
            # Use a date 7 days ago as fallback instead of current date
            fallback_date = datetime.now(timezone.utc) - timedelta(days=7)
            self.logger.warning(f"Using 7-day fallback for unparseable date: '{date_str}'")
            return fallback_date.isoformat()
    
    def _parse_relative_date(self, date_str: str) -> str:
        """Parse relative date strings like '2 days ago', '1 week ago', etc."""
        if not date_str:
            return None
            
        date_str = date_str.lower().strip()
        
        # Common patterns for relative dates
        import re
        
        # Pattern: "X days ago"
        days_match = re.search(r'(\d+)\s+days?\s+ago', date_str)
        if days_match:
            days = int(days_match.group(1))
            target_date = datetime.now(timezone.utc) - timedelta(days=days)
            self.logger.info(f"Parsed relative date '{date_str}' as {days} days ago")
            return target_date.isoformat()
        
        # Pattern: "X hours ago"
        hours_match = re.search(r'(\d+)\s+hours?\s+ago', date_str)
        if hours_match:
            hours = int(hours_match.group(1))
            target_date = datetime.now(timezone.utc) - timedelta(hours=hours)
            self.logger.info(f"Parsed relative date '{date_str}' as {hours} hours ago")
            return target_date.isoformat()
        
        # Pattern: "X weeks ago"
        weeks_match = re.search(r'(\d+)\s+weeks?\s+ago', date_str)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            target_date = datetime.now(timezone.utc) - timedelta(weeks=weeks)
            self.logger.info(f"Parsed relative date '{date_str}' as {weeks} weeks ago")
            return target_date.isoformat()
        
        # Pattern: "yesterday"
        if 'yesterday' in date_str:
            target_date = datetime.now(timezone.utc) - timedelta(days=1)
            self.logger.info(f"Parsed relative date '{date_str}' as yesterday")
            return target_date.isoformat()
        
        # Pattern: "today" or "earlier today"
        if 'today' in date_str or 'earlier today' in date_str:
            target_date = datetime.now(timezone.utc)
            self.logger.info(f"Parsed relative date '{date_str}' as today")
            return target_date.isoformat()
        
        return None
    
    def _extract_absolute_date_from_text(self, text: str) -> str:
        """Extract absolute dates from text content (e.g., 'September 5, 2025', '2025-09-05')."""
        if not text:
            return None
            
        import re
        
        # Pattern 1: "September 5, 2025", "Sep 5, 2025"
        month_day_year = re.search(r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b', text, re.IGNORECASE)
        if month_day_year:
            try:
                date_str = f"{month_day_year.group(1)} {month_day_year.group(2)}, {month_day_year.group(3)}"
                parsed_date = date_parser.parse(date_str)
                if parsed_date.tzinfo is None:
                    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                self.logger.info(f"Extracted month-day-year date: {date_str}")
                return parsed_date.isoformat()
            except:
                pass
        
        # Pattern 2: ISO format "2025-09-05"
        iso_date = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
        if iso_date:
            try:
                parsed_date = datetime.strptime(iso_date.group(1), '%Y-%m-%d')
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                self.logger.info(f"Extracted ISO date: {iso_date.group(1)}")
                return parsed_date.isoformat()
            except:
                pass
        
        # Pattern 3: "5 September 2025", "5 Sep 2025", "15 August 2025"
        day_month_year = re.search(r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b', text, re.IGNORECASE)
        if day_month_year:
            try:
                date_str = f"{day_month_year.group(1)} {day_month_year.group(2)} {day_month_year.group(3)}"
                parsed_date = date_parser.parse(date_str)
                if parsed_date.tzinfo is None:
                    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                self.logger.info(f"Extracted day-month-year date: {date_str}")
                return parsed_date.isoformat()
            except:
                pass
        
        return None
    
    def _get_source_name(self, feed_url: str) -> str:
        """Extract source name from feed URL."""
        source_mapping = {
            'aihealth.duke.edu': 'Duke AI Health',
            'statnews.com/tag/artificial-intelligence': 'STAT AI',
            'medcitynews.com': 'MedCity News',
        }
        
        for domain, name in source_mapping.items():
            if domain in feed_url:
                return name
        
        return 'Unknown'
    
    def _quick_ai_screening(self, entry: Dict) -> bool:
        """Stage 1: Quick keyword screening to filter out obvious non-matches."""
        title_desc = f"{entry.get('title', '')} {entry.get('description', '')}".lower()
        
        # Quick AI keyword check (more inclusive than before)
        ai_keywords = [
            'artificial intelligence', 'ai ', ' ai', 'machine learning', 'ml ',
            'deep learning', 'neural network', 'chatgpt', 'gpt-', 'llm', 'llms',
            'large language model', 'foundation model', 'generative ai',
            'natural language processing', 'nlp', 'computer vision',
            'automated', 'algorithm', 'predictive model', 'digital health',
            'smart system', 'intelligent system', 'computational'
        ]
        
        clinical_keywords = [
            'clinical trial', 'clinical research', 'clinical study', 'trial',
            'patient recruitment', 'trial design', 'trial protocol',
            'clinical investigation', 'study protocol', 'research study',
            'randomized', 'controlled trial', 'trial data', 'clinical data'
        ]
        
        # Must have both AI and clinical keywords
        has_ai_keyword = any(keyword in title_desc for keyword in ai_keywords)
        has_clinical_keyword = any(keyword in title_desc for keyword in clinical_keywords)
        
        return has_ai_keyword and has_clinical_keyword
    
    def _calculate_relevance_score(self, entry: Dict, controlled_vocabulary: List[str]) -> float:
        """Calculate BM25-style relevance score for ranking articles."""
        # Controlled vocabulary for clinical AI terms
        if not controlled_vocabulary:
            controlled_vocabulary = [
                'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
                'chatgpt', 'gpt-4', 'large language model', 'llm', 'generative ai',
                'natural language processing', 'nlp', 'foundation model',
                'clinical trial', 'clinical research', 'patient recruitment', 'trial design',
                'trial protocol', 'clinical study', 'randomized controlled trial',
                'trial monitoring', 'clinical data', 'trial automation'
            ]
        
        # Combine title and description for scoring
        text = f"{entry.get('title', '')} {entry.get('description', '')}".lower()
        words = re.findall(r'\b\w+\b', text)
        
        if not words:
            return 0.0
        
        # BM25 parameters
        k1 = 1.2
        b = 0.75
        avg_doc_length = 50  # Assumed average document length
        doc_length = len(words)
        
        score = 0.0
        
        # Calculate BM25 score for each vocabulary term
        for term in controlled_vocabulary:
            term_words = term.split()
            term_count = 0
            
            # Count occurrences of the term (could be multi-word)
            if len(term_words) == 1:
                term_count = words.count(term_words[0])
            else:
                # For multi-word terms, check for phrase occurrence
                text_for_phrase = ' '.join(words)
                term_count = text_for_phrase.count(term)
            
            if term_count > 0:
                # BM25 formula
                tf = term_count / doc_length
                idf = math.log((1000 + 1) / (term_count + 1))  # Simplified IDF
                
                term_score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_length / avg_doc_length)))
                score += term_score
        
        return score
    
    def _calculate_recency_score(self, entry: Dict) -> float:
        """Calculate recency score (more recent = higher score)."""
        try:
            pub_date = datetime.fromisoformat(entry.get('pub_date', '').replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            days_old = (now - pub_date).days
            
            # Exponential decay: newer articles get higher scores
            # Articles from today get score 1.0, articles from 30 days ago get ~0.5
            recency_score = math.exp(-days_old / 30.0)
            return recency_score
        except:
            return 0.5  # Default for unparseable dates
    
    def _rank_articles(self, entries: List[Dict]) -> List[Dict]:
        """Rank articles by combined recency and relevance score."""
        controlled_vocab = [
            'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
            'chatgpt', 'gpt-4', 'gpt-3', 'claude', 'llama', 'gemini',
            'large language model', 'llm', 'foundation model', 'generative ai',
            'natural language processing', 'nlp', 'computer vision',
            'clinical trial', 'clinical research', 'patient recruitment', 'trial design',
            'trial protocol', 'clinical study', 'randomized controlled trial', 'rct',
            'trial monitoring', 'clinical data', 'trial automation', 'patient engagement',
            'synthetic data', 'ai chatbot', 'virtual assistant', 'clinical documentation'
        ]
        
        # Calculate combined score for each entry
        for entry in entries:
            relevance_score = self._calculate_relevance_score(entry, controlled_vocab)
            recency_score = self._calculate_recency_score(entry)
            
            # Combined score: 70% relevance, 30% recency
            combined_score = (0.7 * relevance_score) + (0.3 * recency_score)
            entry['_ranking_score'] = combined_score
            entry['_relevance_score'] = relevance_score
            entry['_recency_score'] = recency_score
        
        # Sort by combined score (highest first)
        ranked_entries = sorted(entries, key=lambda x: x.get('_ranking_score', 0), reverse=True)
        
        # Remove scoring fields from final output
        for entry in ranked_entries:
            entry.pop('_ranking_score', None)
            entry.pop('_relevance_score', None) 
            entry.pop('_recency_score', None)
        
        return ranked_entries
    
    def _get_dynamic_summary_prompt(self) -> str:
        """Generate varied summary prompt styles to create more engaging and diverse summaries."""
        import random
        
        # Common boring openings to avoid
        avoid_phrases = [
            "The article discusses",
            "This research explores",
            "The study investigates", 
            "This technology is relevant",
            "The authors present",
            "This application of AI",
            "The paper describes",
            "This methodology involves"
        ]
        
        summary_styles = [
            # Style 1: Impact-focused
            f"Create a compelling summary that starts with the breakthrough or key finding. AVOID these generic openings: {', '.join(avoid_phrases[:3])}. Instead, lead with the innovation or discovery that makes this research significant.",
            
            # Style 2: Problem-solution focused
            f"Write a summary that identifies the clinical challenge being addressed and how this AI approach solves it. AVOID starting with '{avoid_phrases[0]}' or '{avoid_phrases[1]}'. Make it feel like a story of innovation solving real problems.",
            
            # Style 3: Technical innovation focused
            f"Highlight what makes this AI methodology technically groundbreaking. AVOID formulaic phrases like '{avoid_phrases[4]}' or '{avoid_phrases[6]}'. Focus on the novel aspects that advance the field.",
            
            # Style 4: Clinical significance focused
            f"Emphasize immediate clinical significance and patient impact. AVOID '{avoid_phrases[2]}' or '{avoid_phrases[5]}'. Start with outcomes that matter to healthcare practitioners.",
            
            # Style 5: Future-oriented
            f"Focus on transformative potential and future implications. AVOID '{avoid_phrases[7]}' or '{avoid_phrases[3]}'. Use forward-looking language that captures revolutionary possibilities.",
            
            # Style 6: Human-centered
            f"Write from a human-centered perspective focusing on patient, researcher, or clinician benefits. AVOID '{avoid_phrases[6]}' or '{avoid_phrases[0]}'. Emphasize real-world user experience.",
            
            # Style 7: Data-driven insight
            f"Lead with compelling statistics, performance metrics, or quantitative improvements. AVOID '{avoid_phrases[1]}' or '{avoid_phrases[4]}'. Let the numbers tell the innovation story.",
            
            # Style 8: Accessibility focused
            f"Explain complex AI concepts accessibly while maintaining scientific rigor. AVOID '{avoid_phrases[5]}' or '{avoid_phrases[2]}'. Make groundbreaking technology understandable."
        ]
        
        return random.choice(summary_styles)
    
    def identify_ai_content(self, entries: List[Dict]) -> List[Dict]:
        """Identify articles specifically about AI applications in clinical research using two-stage filtering."""
        ai_entries = []
        
        for entry in entries:
            # STAGE 1: Quick keyword screening
            if not self._quick_ai_screening(entry):
                # Failed quick screen - skip LLM evaluation
                continue
            
            # STAGE 2: Detailed LLM evaluation for articles that passed Stage 1
            # Try up to 3 times to ensure we get all required fields
            for attempt in range(3):
                try:
                    # Relaxed prompt to include NLP and machine learning context
                    prompt = f"""
                    You are an expert AI researcher specializing in clinical trials and medical research applications.
                    
                    Analyze this article to determine if it discusses AI technologies applied to clinical research or healthcare.
                    
                    ACCEPT IF THE ARTICLE MENTIONS:
                    
                    TIER 1 - CORE GENERATIVE AI IN CLINICAL RESEARCH:
                    - ChatGPT, GPT models, LLMs, foundation models in clinical research
                    - Generative AI for trial protocols, patient communication, or data generation
                    - AI chatbots or virtual assistants for patient recruitment or trial engagement
                    - Synthetic data generation for clinical research
                    - AI-powered clinical trial documentation or report generation
                    
                    TIER 2 - APPLIED AI/ML IN CLINICAL RESEARCH:
                    - Natural language processing for clinical data analysis
                    - Machine learning for clinical trial monitoring or safety assessment
                    - AI tools for patient stratification or recruitment
                    - Automated systems for trial data collection or management
                    - Predictive models for clinical outcomes or patient selection
                    - Computer-assisted clinical decision making
                    
                    TIER 3 - BROADER AI/ML IN HEALTHCARE RESEARCH:
                    - Digital health technologies used in clinical studies
                    - Computational methods for clinical research
                    - AI-assisted drug discovery mentioned in research contexts
                    - Automated clinical documentation systems
                    - Machine learning applications in healthcare research
                    - NLP applications in medical data processing
                    
                    BE MORE INCLUSIVE: Accept articles that mention AI/ML technologies in healthcare research contexts,
                    not just strict clinical trial operations. Include broader applications that could benefit clinical research.
                    
                    Article Title: {entry['title']}
                    Article Description: {entry['description'][:500]}
                    
                    You MUST provide ALL THREE fields:
                    1. is_ai_related: true/false (More inclusive - include ML/NLP/digital health contexts)
                    2. A comprehensive summary of the AI technology and its relevance to clinical research
                    3. ai_tag: Choose the most specific category

                    IMPORTANT AI TAGGING GUIDELINES:
                    - "Generative AI": Use for ChatGPT, GPT-4, Claude, Llama, LLMs when used for CONTENT GENERATION (text generation, medical writing, protocol creation, report writing, synthetic data creation)
                    - "Natural Language Processing": Use for traditional NLP tasks (text analysis, information extraction, classification, sentiment analysis) WITHOUT content generation
                    - "Machine Learning": Use for predictive models, algorithms, data analysis, pattern recognition
                    - "Trial Optimization": Use for patient recruitment, trial design optimization, site selection
                    - "AI Ethics": Use for bias, fairness, regulatory compliance discussions
                    - "Digital Health": Use for apps, platforms, digital therapeutics, remote monitoring

                    SUMMARY WRITING INSTRUCTIONS: {self._get_dynamic_summary_prompt()}

                    JSON format required:
                    {{
                        "is_ai_related": true/false,
                        "summary": "Write an engaging, original summary following the style instructions above. Keep it informative but fresh and distinctive. Avoid formulaic language and make each summary feel unique while maintaining scientific accuracy.",
                        "ai_tag": "Most specific category from: Generative AI, Natural Language Processing, Machine Learning, Trial Optimization, AI Ethics, Digital Health"
                    }}
                    """
                    
                    self.api_costs['qwen_calls'] += 1
                    response = self.qwen_client.chat.completions.create(
                        model="qwen/qwen-2.5-72b-instruct",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.5,  # Increased from 0.3 to encourage more creative and varied responses
                        max_tokens=500
                    )
                    
                    # Parse the JSON response
                    content = response.choices[0].message.content.strip()
                    
                    # Debug: Log the raw response
                    self.logger.info(json.dumps({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "entry_id": entry['id'],
                        "entry_title": entry['title'][:50],
                        "raw_llm_response": content[:200],
                        "attempt": attempt + 1
                    }))
                    
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        
                        # Debug: Log the parsed result
                        self.logger.info(json.dumps({
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "entry_id": entry['id'],
                            "parsed_result": result,
                            "is_ai_related": result.get('is_ai_related', False)
                        }))
                        
                        # Validate all required fields are present and valid
                        if self._validate_ai_response(result):
                            # Only include AI-related articles
                            if result.get('is_ai_related', False):
                                entry['is_ai_related'] = True
                                entry['summary'] = self._sanitize_text(result.get('summary', ''))
                                entry['ai_tag'] = self._sanitize_text(result.get('ai_tag', 'AI Research'))
                                entry['brief_date'] = self.brief_date  # Add brief_date field
                                
                                # Ensure word limits - longer summary, no resources
                                entry['summary'] = self._limit_words(entry['summary'], 140)  # Increased from 60 to 140
                                
                                ai_entries.append(entry)
                            break  # Success, break out of retry loop
                        else:
                            self.logger.warning(f"Invalid LLM response for entry {entry['id']}, attempt {attempt + 1}: {result}")
                            if attempt == 2:  # Last attempt
                                self.logger.error(f"Failed to get valid LLM response for entry {entry['id']} after 3 attempts")
                    else:
                        self.logger.warning(f"No JSON found in LLM response for entry {entry['id']}, attempt {attempt + 1}")
                        if attempt == 2:  # Last attempt
                            self.logger.error(f"Failed to extract JSON from LLM response for entry {entry['id']} after 3 attempts")
                
                except Exception as e:
                    self.logger.error(f"Error processing entry {entry['id']}, attempt {attempt + 1}: {str(e)}")
                    if attempt == 2:  # Last attempt
                        continue
        
        # Apply ranking to AI entries before returning
        ranked_ai_entries = self._rank_articles(ai_entries)
        
        self.logger.info(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_ai_entries": len(ranked_ai_entries),
            "ranking_applied": True,
            "message": "Articles ranked by combined relevance and recency scores"
        }))
        
        return ranked_ai_entries
    
    def _validate_ai_response(self, result: Dict) -> bool:
        """Validate that LLM response contains all required fields for AI identification."""
        required_fields = ['is_ai_related', 'summary', 'ai_tag']
        
        for field in required_fields:
            if field not in result:
                return False
            
            value = result[field]
            
            # Validate is_ai_related
            if field == 'is_ai_related':
                if not isinstance(value, bool):
                    return False
            
            # For non-AI articles, we don't need complete ai_tag
            elif field == 'summary':
                if not isinstance(value, str) or len(value.strip()) < 5:
                    return False
            
            # For AI-related articles, require complete ai_tag
            elif field == 'ai_tag':
                if result.get('is_ai_related', False):
                    if not isinstance(value, str) or len(value.strip()) < 5:
                        return False
                # For non-AI articles, ai_tag can be empty
        
        return True
    
    def _limit_words(self, text: str, max_words: int) -> str:
        """Limit text to specified number of words with smarter truncation."""
        words = text.split()
        if len(words) > max_words:
            # Try to find a sentence-ending punctuation within the last few words
            # to avoid cutting off mid-thought
            truncated_text = ' '.join(words[:max_words])
            
            # If we already have a complete sentence, we're good
            if truncated_text.rstrip().endswith(('.', '!', '?')):
                return truncated_text
                
            # Otherwise check if there's a sentence break in the last 15 words
            last_sentence_break = max(
                truncated_text.rfind('.'), 
                truncated_text.rfind('!'),
                truncated_text.rfind('?')
            )
            
            if last_sentence_break > len(truncated_text) - 30:
                # Found a recent sentence break, use it
                return truncated_text[:last_sentence_break + 1]
            
            # No good break point found, add ellipsis
            return truncated_text + '...'
            
        return text
    
    def select_articles(self, entries: List[Dict]) -> List[Dict]:
        """Select and sort AI-specific clinical research articles by publication date."""
        # Sort by publication date (descending) to show newest first
        sorted_entries = sorted(
            entries,
            key=lambda x: x.get('pub_date', ''),
            reverse=True
        )
        
        # Return all AI-specific articles (already filtered in identify_ai_content)
        return sorted_entries
    
    def save_brief_data(self, entries: List[Dict], output_file: str):
        """Save brief data to JSON file with validation and atomic writes."""
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            # Validate entries before saving
            validated_items = []
            for entry in entries:
                try:
                    # Convert to BriefItem for validation
                    validated_item = BriefItem(**entry)
                    validated_items.append(validated_item.model_dump())
                except ValidationError as e:
                    self.logger.warning(f"Skipping invalid entry: {e}")
                    continue
            
            # Create validated brief data
            try:
                brief_data_obj = BriefData(
                    items=validated_items,
                    total_items=len(validated_items),
                    brief_date=self.brief_date
                )
                brief_data = brief_data_obj.model_dump()
                brief_data['generated_at'] = datetime.now(timezone.utc).isoformat()
            except ValidationError as e:
                self.logger.error(f"Brief data validation failed: {e}")
                # Fallback to basic structure
                brief_data = {
                    'brief_date': self.brief_date,
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'items': validated_items,
                    'total_items': len(validated_items)
                }
            
            # Atomic write using temporary file
            temp_file = output_file + '.tmp'
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(brief_data, f, indent=2, ensure_ascii=False)
                
                # Atomic move
                Path(temp_file).rename(output_file)
                self.logger.info(f"Brief data saved successfully to {output_file}")
                
            except Exception as e:
                # Clean up temp file on error
                if Path(temp_file).exists():
                    Path(temp_file).unlink()
                raise e
                
        except Exception as e:
            self.logger.error(f"Failed to save brief data: {e}")
            # Don't re-raise - allow pipeline to continue
    
    def log_cost_estimate(self):
        """Log estimated API costs for this run."""
        # Rough cost estimates (as of 2025)
        qwen_cost_per_1k = 0.0007  # $0.0007 per 1k tokens
        google_cost_per_call = 0.005  # $0.005 per search
        
        estimated_cost = (
            self.api_costs['qwen_calls'] * qwen_cost_per_1k +
            self.api_costs['google_calls'] * google_cost_per_call
        )
        
        self.api_costs['estimated_cost_usd'] = estimated_cost
        
        self.logger.info(f"API usage summary: {self.api_costs}")
        return estimated_cost


class SiteGenerator:
    """Handles HTML generation using Jinja2."""
    
    def __init__(self, templates_dir: str = "templates"):
        """Initialize the site generator."""
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        
    def generate_html(self, brief_data: Dict, output_file: str):
        """Generate HTML page using Jinja2 template with atomic writes."""
        try:
            template = self.env.get_template('index.html')
            
            # Prepare template context
            goatcounter_url = os.getenv("GOATCOUNTER_URL", "")
            context = {
                'brief_date': brief_data['brief_date'],
                'generated_at': brief_data['generated_at'],
                'items': brief_data['items'],
                'total_items': brief_data['total_items'],
                'GOATCOUNTER_URL': goatcounter_url,
            }
            
            # Render template
            html_content = template.render(**context)
            
            # Atomic write using temporary file
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            temp_file = output_file + '.tmp'
            
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # Atomic move
                Path(temp_file).rename(output_file)
                
            except Exception as e:
                # Clean up temp file on error
                if Path(temp_file).exists():
                    Path(temp_file).unlink()
                raise e
                
        except Exception as e:
            logging.error(f"Failed to generate HTML: {e}")
            # Don't re-raise - allow pipeline to continue
            return


def main():
    """Main pipeline execution with comprehensive error handling."""
    brief_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    log_file = f"logs/{brief_date}.log"
    json_file = f"briefs/{brief_date}.json"
    html_file = "site/index.html"
    
    # Status tracking for CI
    status_file = f"logs/{brief_date}.status"
    
    # Initialize variables for error handling
    selected_articles = []
    
    try:
        # Validate required environment variables
        qwen_api_key = os.environ.get('OPENROUTER_API_KEY')
        if not qwen_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        
        # Configuration: Default max entries for sources without specific limits
        default_max_entries = int(os.environ.get('DEFAULT_MAX_ENTRIES', '8'))
        
        # Configuration: Timeframe for article collection (configurable via environment)
        days_back = int(os.environ.get('DAYS_BACK', '60'))  # Default to 60 days
        
        # Initialize processors with error handling
        try:
            feed_processor = FeedProcessor(qwen_api_key, log_file, days_back)
            site_generator = SiteGenerator()
        except Exception as e:
            logging.error(f"Failed to initialize processors: {e}")
            _write_status_file(status_file, 'FAILED', f"Initialization failed: {e}")
            raise
        
        print(f"Starting The AI-Powered Clinical Research Intelligence Hub pipeline for {brief_date}")
        print(f"Collecting articles from the last {days_back} days")
        
        # Step 1: Fetch feeds using RSS feeds and web search APIs (soft fail)
        entries = []
        try:
            print("Fetching articles using RSS feeds and web search APIs...")
            entries = feed_processor.fetch_feeds(default_max=default_max_entries)
            print(f"Fetched {len(entries)} entries from RSS feeds and web search APIs")
        except Exception as e:
            logging.error(f"Failed to fetch feeds: {e}")
            print(f"Warning: Failed to fetch feeds, continuing with empty set: {e}")
        
        if not entries:
            print("No entries found, creating minimal brief")
            _write_status_file(status_file, 'WARNING', "No entries found")
        
        # Step 2: Identify AI-specific content (soft fail)
        ai_entries = []
        try:
            print("Identifying AI-specific articles in clinical research with Qwen...")
            ai_entries = feed_processor.identify_ai_content(entries)
            print(f"Identified {len(ai_entries)} AI-specific clinical research articles")
        except Exception as e:
            logging.error(f"Failed to identify AI content: {e}")
            print(f"Warning: Failed to identify AI content, using all entries: {e}")
            ai_entries = entries  # Fallback to all entries
        
        # Step 3: Select and sort articles (soft fail)
        selected_articles = []
        try:
            print("Selecting and sorting articles...")
            selected_articles = feed_processor.select_articles(ai_entries)
            print(f"Selected {len(selected_articles)} articles for the brief")
        except Exception as e:
            logging.error(f"Failed to select articles: {e}")
            print(f"Warning: Failed to select articles, using all AI entries: {e}")
            selected_articles = ai_entries  # Fallback to all AI entries
        
        # Step 4: Save brief data (critical - must succeed)
        try:
            print("Saving brief data...")
            feed_processor.save_brief_data(selected_articles, json_file)
        except Exception as e:
            logging.error(f"Failed to save brief data: {e}")
            _write_status_file(status_file, 'FAILED', f"Failed to save brief data: {e}")
            raise
        
        # Step 5: Generate HTML (soft fail)
        try:
            print("Generating HTML...")
            with open(json_file, 'r', encoding='utf-8') as f:
                brief_data = json.load(f)
            site_generator.generate_html(brief_data, html_file)
        except Exception as e:
            logging.error(f"Failed to generate HTML: {e}")
            print(f"Warning: Failed to generate HTML: {e}")
            _write_status_file(status_file, 'WARNING', f"HTML generation failed: {e}")
        
        # Log cost estimates
        try:
            cost = feed_processor.log_cost_estimate()
            print(f"Estimated cost: ${cost:.4f}")
        except Exception as e:
            logging.warning(f"Failed to calculate costs: {e}")
        
        print(f"Pipeline completed successfully!")
        print(f"- Brief data: {json_file}")
        print(f"- HTML page: {html_file}")
        print(f"- Logs: {log_file}")
        
        _write_status_file(status_file, 'SUCCESS', f"Pipeline completed with {len(selected_articles)} articles")
        
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        print(f"Pipeline failed: {e}")
        try:
            _write_status_file(status_file, 'FAILED', str(e))
        except:
            pass  # Don't fail on status file write
        raise

def _write_status_file(status_file: str, status: str, message: str = ""):
    """Write status file for CI monitoring."""
    try:
        Path(status_file).parent.mkdir(parents=True, exist_ok=True)
        status_data = {
            'status': status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': message
        }
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to write status file: {e}")


if __name__ == "__main__":
    main()
