#!/usr/bin/env python
# coding: utf-8

"""
Web scraping functionality for the Website Summary Tool
"""

import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from config.constants import HTTP_HEADERS
from structures.models import Website


def fetch_website_content_simple(url):
    """
    Fetch website content using requests and BeautifulSoup.
    
    Args:
        url: The URL to fetch
        
    Returns:
        tuple: (Website object containing the parsed content, needs_selenium)
    """
    response = requests.get(url, headers=HTTP_HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract title
    title = soup.title.string if soup.title else "No title found"
    
    # Check if the page might need Selenium
    needs_selenium = detect_needs_selenium(soup, response.text)
    
    # Clean up content
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = "No body content found"
    
    return Website(url, title, text), needs_selenium

def detect_needs_selenium(soup, html_content):
    """
    Detect if a webpage likely needs Selenium for proper rendering.
    
    Args:
        soup: BeautifulSoup object
        html_content: Raw HTML content
        
    Returns:
        bool: True if the page likely needs Selenium
    """
    # Check for SPA frameworks
    spa_indicators = [
        'ng-app', 'ng-controller',  # Angular
        'react', 'reactjs',         # React
        'vue', 'v-app', 'v-if',     # Vue
        'ember'                     # Ember
    ]
    
    # Check for loading indicators or placeholders
    loading_indicators = [
        'loading', 'please wait', 'spinner',
        'content is loading', 'loading content'
    ]
    
    # Check for scripts that might dynamically load content
    scripts = soup.find_all('script')
    dynamic_content_indicators = [
        'document.write', '.innerHTML', 'appendChild',
        'fetch(', 'XMLHttpRequest', 'ajax', '.load(', 
        'getElementById', 'querySelector'
    ]
    
    # Check for minimal text content
    text_content = soup.get_text().strip()
    min_content_length = 500  # Arbitrary threshold
    
    # Check for meta tags indicating spa/js app
    meta_tags = soup.find_all('meta')
    meta_spa_indicators = ['single page application', 'javascript application', 'react application', 'vue application']
    
    # SPA framework indicators
    for attr in spa_indicators:
        if attr in html_content.lower():
            return True
    
    # Check meta tags
    for meta in meta_tags:
        content = meta.get('content', '').lower()
        for indicator in meta_spa_indicators:
            if indicator in content:
                return True
    
    # Check for loading indicators or placeholders
    for indicator in loading_indicators:
        if indicator in html_content.lower():
            return True
    
    # Check for dynamic content loading scripts
    script_text = ' '.join([script.string for script in scripts if script.string])
    for indicator in dynamic_content_indicators:
        if indicator in script_text:
            return True
    
    # Check if the page has minimal text content but many scripts
    if len(text_content) < min_content_length and len(scripts) > 5:
        return True
    
    # Check for lazy-loaded content
    if re.search(r'lazy[\s-]load|lazyload', html_content, re.IGNORECASE):
        return True
        
    return False

def fetch_website_content_selenium(url):
    """
    Fetch website content using Selenium for JavaScript-heavy websites.
    
    Args:
        url: The URL to fetch
        
    Returns:
        Website: A Website object containing the parsed content
    """
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless=new")  # Updated headless mode syntax
    
    # Use the built-in Selenium Manager instead of explicit driver path
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        
        # Wait for dynamic content to load
        driver.implicitly_wait(5)  # Wait up to 5 seconds
        
        # Check if there's a verification or captcha
        if detect_verification_needed(driver):
            # Switch to interactive mode if verification is needed
            driver.quit()
            
            # Restart with visible browser for user interaction
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            input("Please complete the verification in the browser and press Enter to continue...")
        
        page_source = driver.page_source
    finally:
        driver.quit()
    
    soup = BeautifulSoup(page_source, 'html.parser')
    title = soup.title.string if soup.title else "No title found"
    
    for irrelevant in soup(["script", "style", "img", "input"]):
        irrelevant.decompose()
    
    text = soup.get_text(separator="\n", strip=True)
    
    return Website(url, title, text)

def detect_verification_needed(driver):
    """
    Detect if the page requires human verification.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        bool: True if verification appears to be needed
    """
    page_source = driver.page_source.lower()
    verification_indicators = [
        'captcha', 'recaptcha', 'human verification', 
        'verify you are human', 'bot check', 'security check',
        'prove you are human', 'complete the security check',
        'verification required', 'verification needed'
    ]
    
    for indicator in verification_indicators:
        if indicator in page_source:
            return True
    
    # Check for typical captcha elements
    try:
        captcha_elements = driver.find_elements(By.XPATH,
            "//*[contains(@id, 'captcha') or contains(@class, 'captcha') or contains(@name, 'captcha')]"
        )
        if captcha_elements:
            return True
    except Exception:
        pass
    
    return False

def fetch_website_content(url, use_selenium=None):
    """
    Fetch website content using the appropriate method.
    
    Args:
        url: The URL to fetch
        use_selenium: Whether to use Selenium for JavaScript-heavy websites.
                     If None, automatic detection is used.
                     If True, always use Selenium.
                     If False, never use Selenium.
        
    Returns:
        Website: A Website object containing the parsed content
    """
    # If explicit user preference is provided, respect it
    if use_selenium is True:
        return fetch_website_content_selenium(url)
    elif use_selenium is False:
        website, _ = fetch_website_content_simple(url)
        return website
    
    # Otherwise, use automatic detection
    website, needs_selenium = fetch_website_content_simple(url)
    
    if needs_selenium:
        print(f"Detected JavaScript-heavy website, switching to Selenium for better content extraction...")
        return fetch_website_content_selenium(url)
    
    return website