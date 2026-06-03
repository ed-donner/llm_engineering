"""
ARIA configuration: watchlist, API keys, thresholds, market hours.
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Watchlist (user can override via ARIA_WATCHLIST env, comma-separated)
_DEFAULT_WATCHLIST = [
    "XAU/USD", "XAG/USD", "WTI", "Copper",  # Commodities
    "AAPL", "NVDA", "MSFT", "TSLA", "META",  # Stocks
    "SPX", "NDX", "DJI",  # Indices
    "BTC/USD", "ETH/USD",  # Crypto
]

def get_watchlist() -> list[str]:
    raw = os.getenv("ARIA_WATCHLIST", "")
    if raw.strip():
        return [s.strip() for s in raw.split(",") if s.strip()]
    return _DEFAULT_WATCHLIST.copy()

# Assets that trade 24/7 (alert outside US market hours)
ASSETS_24_7 = {"XAU/USD", "XAG/USD", "WTI", "Copper", "BTC/USD", "ETH/USD"}

# US market hours ET (for scheduling and alert gating)
MARKET_OPEN_HOUR_ET = 9
MARKET_CLOSE_HOUR_ET = 17  # 5pm

# Alert thresholds
ALERT_SCORE_THRESHOLD = 65
MAX_ALERTS_PER_HOUR = 3
ASSET_COOLDOWN_HOURS = 2
SCORE_BUMP_TO_OVERRIDE_COOLDOWN = 15

# API keys (from env)
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
# CommodityPriceAPI for gold/silver (replaces Metals-API)
COMMODITY_PRICE_API_KEY = os.getenv("COMMODITY_PRICE_API_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
PUSHOVER_USER = os.getenv("PUSHOVER_USER", "")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN", "")

# OpenRouter for all LLM calls (sentiment)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
# LiteLLM model string: use openrouter/ prefix so litellm uses OPENROUTER_API_KEY
SENTIMENT_MODEL = os.getenv("ARIA_SENTIMENT_MODEL", "openrouter/openai/gpt-5-nano")
