"""
Data collection modules for market, economic, and news data
"""

from .market_data import get_market_data, get_sector_performance, get_fear_greed_index, get_polymarket_data, is_market_open
from .economic_data import get_economic_indicators
from .news_data import get_news_articles
from .earnings_data import get_earnings_sentiment

__all__ = [
    'get_market_data',
    'get_sector_performance',
    'get_fear_greed_index',
    'get_polymarket_data',
    'is_market_open',
    'get_economic_indicators',
    'get_news_articles',
    'get_earnings_sentiment'
]


