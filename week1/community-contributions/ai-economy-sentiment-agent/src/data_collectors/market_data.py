"""
Market data collection using yfinance and CNN Fear & Greed Index
"""

import yfinance as yf
import requests
from datetime import datetime
import pytz
from typing import Dict, Tuple, Any, List

from config import (
    MARKET_TICKERS,
    SECTOR_ETFS,
    FEAR_GREED_URL, 
    HEADERS, 
    POLYMARKET_API_URL, 
    POLYMARKET_FETCH_LIMIT
)
from src.logger import log


def is_market_open() -> bool:
    """
    Check if US stock market is currently open.
    
    Returns:
        bool: True if market is open, False otherwise
    """
    try:
        eastern = pytz.timezone('US/Eastern')
        now = datetime.now(eastern)
        
        # Market closed on weekends
        if now.weekday() >= 5:
            return False
        
        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    except Exception:
        return False


def get_market_data() -> Dict[str, Any]:
    """
    Fetch current market data for major indices using yfinance.
    
    Returns:
        Dict containing market data for S&P 500, Nasdaq-100 (QQQ), and VIX
    """
    market_data = {}
    market_open = is_market_open()
    
    log.normal("Fetching market data...")
    
    for name, ticker in MARKET_TICKERS.items():
        try:
            stock = yf.Ticker(ticker)
            
            if market_open:
                # Get current price
                current_price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
                previous_close = stock.info.get('previousClose')
                
                if current_price and previous_close:
                    daily_change = ((current_price - previous_close) / previous_close) * 100
                    market_data[name] = {
                        'current_price': current_price,
                        'previous_close': previous_close,
                        'daily_change_pct': daily_change,
                        'is_live': True
                    }
                    log.verbose(f"[OK] {name} ({ticker}): ${current_price:.2f} ({daily_change:+.2f}%)")
                else:
                    raise ValueError("Price data unavailable")
            else:
                # Market closed - get last close
                hist = stock.history(period="5d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
                    daily_change = ((current_price - previous_price) / previous_price) * 100
                    
                    market_data[name] = {
                        'current_price': current_price,
                        'previous_close': previous_price,
                        'daily_change_pct': daily_change,
                        'is_live': False
                    }
                    log.verbose(f"[OK] {name} ({ticker}): ${current_price:.2f} ({daily_change:+.2f}%) [Last Close]")
                else:
                    raise ValueError("No historical data available")
                    
        except Exception as e:
            market_data[name] = None
            log.error(f"[WARN] {name} ({ticker}): Error - {str(e)[:50]}")
    
    log.minimal("")  # Blank line for readability
    return market_data


def get_sector_performance() -> Dict[str, Any]:
    """
    Fetch performance data for all 11 S&P 500 sectors.
    Identifies sector rotation and market leadership.
    
    Returns:
        Dict containing sector performance data with daily and weekly changes
    """
    sector_data = {}
    
    log.normal("Fetching sector performance...")
    
    for sector, ticker in SECTOR_ETFS.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                previous_price = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
                daily_change = ((current_price - previous_price) / previous_price) * 100
                
                # Get week performance
                week_change = 0
                if len(hist) >= 5:
                    week_start = hist['Close'].iloc[0]
                    week_change = ((current_price - week_start) / week_start) * 100
                
                sector_data[sector] = {
                    'ticker': ticker,
                    'price': current_price,
                    'daily_change_pct': daily_change,
                    'week_change_pct': week_change
                }
                
                log.verbose(f"  {sector:25s} ({ticker}): {daily_change:+.2f}% (day), {week_change:+.2f}% (week)")
            else:
                sector_data[sector] = None
                log.error(f"[WARN] {sector}: No data available")
                
        except Exception as e:
            sector_data[sector] = None
            log.error(f"[WARN] {sector}: Error - {str(e)[:50]}")
    
    # Identify leaders and laggards
    valid_sectors = [(s, d) for s, d in sector_data.items() if d is not None]
    if valid_sectors:
        sorted_daily = sorted(valid_sectors, key=lambda x: x[1]['daily_change_pct'], reverse=True)
        sorted_weekly = sorted(valid_sectors, key=lambda x: x[1]['week_change_pct'], reverse=True)
        
        log.normal(f"  Leader (Daily): {sorted_daily[0][0]} ({sorted_daily[0][1]['daily_change_pct']:+.2f}%)")
        log.normal(f"  Laggard (Daily): {sorted_daily[-1][0]} ({sorted_daily[-1][1]['daily_change_pct']:+.2f}%)")
        
        sector_data['leaders'] = {
            'daily_best': sorted_daily[0][0],
            'daily_worst': sorted_daily[-1][0],
            'weekly_best': sorted_weekly[0][0],
            'weekly_worst': sorted_weekly[-1][0]
        }
    
    log.minimal("")  # Blank line
    return sector_data


def get_fear_greed_index() -> Tuple[float, str]:
    """
    Fetch the CNN Fear & Greed Index.
    
    Returns:
        Tuple of (score: float, rating: str)
        Score ranges from 0 (Extreme Fear) to 100 (Extreme Greed)
    """
    try:
        response = requests.get(FEAR_GREED_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        score = data['fear_and_greed']['score']
        rating = data['fear_and_greed']['rating']
        
        return score, rating
    except Exception as e:
        print(f"[WARN] Fear & Greed Index: Error - {str(e)[:50]}")
        return None, None


def get_polymarket_data() -> List[Dict[str, Any]]:
    """
    Fetch raw Polymarket prediction market data using Gamma API.
    
    Gamma is Polymarket's market metadata and indexing service that provides
    better categorization and filtering than the CLOB API.
    
    Returns:
        List of market dictionaries from Polymarket Gamma API
    """
    try:
        # Use Gamma API - Polymarket's market metadata service
        # https://docs.polymarket.com/developers/gamma-markets-api/overview
        print("Fetching Polymarket data from Gamma API...")
        
        # Gamma API endpoints
        markets_url = f"{POLYMARKET_API_URL}/markets"
        
        # Try multiple filtering strategies to get economic markets
        
        # Strategy 1: Try with economic-related tags (prioritize Economics)
        economic_tags = ['Economics', 'Finance', 'Business', 'Politics', 'US Politics']
        for tag in economic_tags:
            try:
                params = {
                    'closed': 'false',
                    'limit': POLYMARKET_FETCH_LIMIT,
                    'active': 'true',
                    'tag': tag
                }
                
                print(f"  Trying tag '{tag}'...")
                response = requests.get(markets_url, params=params, headers=HEADERS, timeout=20)
                response.raise_for_status()
                
                markets = response.json()
                
                if isinstance(markets, dict):
                    markets = markets.get('data', markets.get('markets', []))
                
                if markets and len(markets) > 5:  # Need at least 5 markets
                    print(f"  [OK] Got {len(markets)} markets with tag '{tag}'")
                    return markets
                    
            except Exception:
                continue
        
        # Strategy 2: Try basic active filter without tag
        try:
            params = {
                'closed': 'false',
                'limit': POLYMARKET_FETCH_LIMIT,
                'active': 'true'
            }
            
            print(f"  Requesting active markets (no tag filter)...")
            response = requests.get(markets_url, params=params, headers=HEADERS, timeout=20)
            response.raise_for_status()
            
            markets = response.json()
            
            if isinstance(markets, dict):
                markets = markets.get('data', markets.get('markets', []))
            
            if markets and len(markets) > 0:
                print(f"  [OK] Got {len(markets)} active markets")
                return markets
                
        except Exception as e:
            print(f"  [INFO] Active filter failed: {str(e)[:60]}")
        
        # Fallback: Try without filters
        try:
            print(f"  Trying Gamma API without filters...")
            response = requests.get(markets_url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            
            markets = response.json()
            
            if isinstance(markets, dict):
                markets = markets.get('data', markets.get('markets', []))
            
            if markets and len(markets) > 0:
                print(f"  [OK] Got {len(markets)} markets from Gamma API (unfiltered)")
                return markets
                
        except Exception as e:
            print(f"  [WARN] Gamma API unfiltered request failed: {str(e)[:60]}")
        
        print("[WARN] No markets data available from Polymarket Gamma API")
        return []
            
    except Exception as e:
        print(f"[WARN] Polymarket Gamma API: Error - {str(e)[:80]}")
        return []

