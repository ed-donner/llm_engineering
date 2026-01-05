"""
Economic indicators scraper from Federal Reserve Economic Data (FRED)
"""

import requests
import time
from bs4 import BeautifulSoup
from typing import Dict, Optional

from config import ECONOMIC_INDICATORS, HEADERS


def scrape_fred_indicator(url: str, indicator_name: str) -> Optional[float]:
    """
    Scrape a single economic indicator from FRED website.
    
    Args:
        url: FRED series URL
        indicator_name: Name of the indicator (for logging)
    
    Returns:
        Float value of the indicator or None if scraping fails
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        obs_value = soup.find('span', {'class': 'series-meta-observation-value'})
        
        if obs_value:
            value_text = obs_value.text.strip().replace(',', '')
            value = float(value_text)
            print(f"[OK] {indicator_name}: {value}")
            return value
        else:
            print(f"[WARN] {indicator_name}: Could not fetch")
            return None
            
    except Exception as e:
        print(f"[WARN] {indicator_name}: Error - {str(e)[:50]}")
        return None


def get_economic_indicators() -> Dict[str, Optional[float]]:
    """
    Fetch all economic indicators from FRED.
    
    Returns:
        Dictionary containing:
        - federal_funds_rate
        - cpi_latest
        - unemployment_rate
        - treasury_10y_yield
        - non_farm_payrolls
    """
    indicators = {}
    
    print("\nFetching economic indicators from FRED...\n")
    
    # 1. Federal Funds Rate
    indicators['federal_funds_rate'] = scrape_fred_indicator(
        ECONOMIC_INDICATORS['federal_funds_rate'],
        "Federal Funds Rate"
    )
    time.sleep(0.5)
    
    # 2. CPI (Consumer Price Index)
    cpi = scrape_fred_indicator(
        ECONOMIC_INDICATORS['cpi'],
        "CPI Index"
    )
    if cpi:
        indicators['cpi_latest'] = cpi
        print(f"  (Note: For YoY inflation %, use official BLS reports)")
    else:
        indicators['cpi_latest'] = None
    time.sleep(0.5)
    
    # 3. Unemployment Rate
    indicators['unemployment_rate'] = scrape_fred_indicator(
        ECONOMIC_INDICATORS['unemployment_rate'],
        "Unemployment Rate"
    )
    time.sleep(0.5)
    
    # 4. 10-Year Treasury Yield
    indicators['treasury_10y_yield'] = scrape_fred_indicator(
        ECONOMIC_INDICATORS['treasury_10y'],
        "10-Year Treasury Yield"
    )
    time.sleep(0.5)
    
    # 5. Non-Farm Payrolls
    payrolls = scrape_fred_indicator(
        ECONOMIC_INDICATORS['non_farm_payrolls'],
        "Non-Farm Payrolls (thousands)"
    )
    if payrolls:
        indicators['non_farm_payrolls'] = payrolls
        print(f"  (Most recent monthly employment figure)")
    else:
        indicators['non_farm_payrolls'] = None
    
    return indicators

