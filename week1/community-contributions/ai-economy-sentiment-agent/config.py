"""
Configuration settings for the AI Economy Sentiment Agent
"""

# Logging Configuration
# Options: "MINIMAL", "NORMAL", "VERBOSE"
# - MINIMAL: Only show final results and errors
# - NORMAL: Show key milestones and summaries (recommended)
# - VERBOSE: Show all debug information and detailed progress
LOG_LEVEL = "NORMAL"

# AI Model Configuration
OLLAMA_BASE_URL = "http://localhost:11434/v1"
AI_MODEL = "gpt-oss"

# Market Tickers - Major Indices
MARKET_TICKERS = {
    "S&P 500": "^GSPC",
    "Nasdaq-100": "QQQ",
    "VIX": "^VIX"
}

# Sector ETFs - All 11 S&P 500 Sectors
SECTOR_ETFS = {
    "Technology": "XLK",
    "Financials": "XLF",
    "Healthcare": "XLV",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Materials": "XLB",
    "Communication Services": "XLC"
}

# News RSS Feeds
RSS_FEEDS = {
    'Economy': 'https://news.google.com/rss/search?q=economy+finance+market+when:7d&hl=en-US&gl=US&ceid=US:en',
    'Politics': 'https://news.google.com/rss/search?q=politics+federal+reserve+inflation+when:7d&hl=en-US&gl=US&ceid=US:en'
}

# Economic Data URLs (FRED)
ECONOMIC_INDICATORS = {
    'federal_funds_rate': 'https://fred.stlouisfed.org/series/DFF',
    'cpi': 'https://fred.stlouisfed.org/series/CPIAUCSL',
    'unemployment_rate': 'https://fred.stlouisfed.org/series/UNRATE',
    'treasury_10y': 'https://fred.stlouisfed.org/series/DGS10',
    'non_farm_payrolls': 'https://fred.stlouisfed.org/series/PAYEMS'
}

# Fear & Greed Index URL
FEAR_GREED_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

# Request Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

# News Configuration
MAX_ARTICLES_PER_CATEGORY = 15  # Articles to fetch per RSS feed
MAX_SELECTED_ARTICLES = 12      # Articles for AI to analyze

# Polymarket Configuration
POLYMARKET_API_URL = "https://gamma-api.polymarket.com"
POLYMARKET_FETCH_LIMIT = 1000      # Markets to fetch from API
POLYMARKET_FILTER_LIMIT = 50       # Max economic markets to pass to AI (limit for performance)
POLYMARKET_SELECTED_MARKETS = 15   # Markets for AI to select (will be deduplicated to ~8-10)

# AI Agent Timeouts
AI_TIMEOUT_SECONDS = 200  # Timeout for AI requests (increased for Polymarket selection)

