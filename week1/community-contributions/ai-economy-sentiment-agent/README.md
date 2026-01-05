# AI Economy Sentiment Agent

A production-quality Python package for comprehensive market sentiment analysis using AI-powered data synthesis.

## Features

### Data Sources
- **Market Performance** - Real-time/delayed prices via yfinance
  - Major indices (S&P 500, Nasdaq-100, VIX)
  - All 11 S&P 500 sectors (XLK, XLF, XLV, XLE, etc.)
- **Market Sentiment**
  - CNN Fear & Greed Index
  - Polymarket prediction markets (AI-curated)
  - Earnings sentiment from major corporations
- **Economic Indicators** - Federal Reserve Economic Data (FRED)
  - Fed Funds Rate, CPI, Unemployment, Treasury Yields, NFP
- **News Analysis** - Google News RSS + AI curation

### Multi-Agent AI Workflow
- **Agent 1**: Curates most relevant news articles (12 from 30+)
- **Agent 2**: Selects most relevant Polymarket predictions (10-15 from 50+)
- **Agent 3**: Analyzes sentiment of selected articles
- **Agent 4**: Synthesizes comprehensive market analysis

### Advanced Features
- ✅ Intelligent Polymarket filtering (removes sports, crypto tech, entertainment)
- ✅ Automatic deduplication (removes repetitive prediction market series)
- ✅ Sector rotation analysis (identifies market leadership)
- ✅ Configurable logging (MINIMAL, NORMAL, VERBOSE)
- ✅ Clean modular architecture
- ✅ Production-ready error handling

---

## Installation

### Prerequisites
- Python 3.11+
- Ollama running locally (or OpenAI API key)

### Setup

1. **Clone the repository**
```bash
cd week1/community-contributions/ai-economy-sentiment-agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Ollama (if using local model)**
   - Start Ollama server: `ollama serve`
   - Pull model: `ollama pull llama3.1`
   - Update `config.py` with your model name

4. **Run the analysis**
```bash
jupyter notebook analysis.ipynb
```

---

## Usage

### Quick Start (Jupyter Notebook)
Open and run `analysis.ipynb` - each cell is documented and runs sequentially.

### Programmatic Usage

```python
from src.data_collectors import (
    get_market_data, get_sector_performance, 
    get_fear_greed_index, get_polymarket_data,
    get_earnings_sentiment, get_economic_indicators,
    get_news_articles
)
from src.ai_agents import (
    select_relevant_articles, select_relevant_polymarkets,
    analyze_news_sentiment, generate_comprehensive_analysis
)

# Collect data
market_data = get_market_data()
sector_data = get_sector_performance()
fear_greed = get_fear_greed_index()
polymarket_raw = get_polymarket_data()
polymarket = select_relevant_polymarkets(polymarket_raw)
earnings = get_earnings_sentiment()
economic_data = get_economic_indicators()
news_articles = get_news_articles()

# AI analysis
selected = select_relevant_articles(news_articles)
news_sentiment = analyze_news_sentiment(selected)

# Comprehensive synthesis
analysis = generate_comprehensive_analysis(
    market_data=market_data,
    sector_data=sector_data,
    fear_greed=fear_greed,
    polymarket=polymarket,
    earnings=earnings,
    economic_data=economic_data,
    news_sentiment=news_sentiment,
    market_is_open=True
)

print(analysis)
```

---

## Configuration

Edit `config.py` to customize:

### Logging Level
```python
LOG_LEVEL = "NORMAL"  # Options: "MINIMAL", "NORMAL", "VERBOSE"
```

- **MINIMAL**: Only final results and errors
- **NORMAL**: Key milestones and progress (recommended)
- **VERBOSE**: All debug information

### AI Model
```python
OLLAMA_BASE_URL = "http://localhost:11434/v1"
AI_MODEL = "gpt-oss"  # Or your preferred Ollama model
```

### Data Sources
```python
# Customize market tickers
MARKET_TICKERS = {
    "S&P 500": "^GSPC",
    "Nasdaq-100": "QQQ",
    "VIX": "^VIX"
}

# All 11 S&P sectors tracked automatically
SECTOR_ETFS = {
    "Technology": "XLK",
    "Financials": "XLF",
    # ... etc
}

# Customize news feeds
RSS_FEEDS = {
    'Economy': 'https://news.google.com/rss/search?q=economy...',
    'Politics': 'https://news.google.com/rss/search?q=politics...'
}
```

---

## Project Structure

```
ai-economy-sentiment-agent/
├── config.py                   # Configuration settings
├── requirements.txt            # Dependencies
├── analysis.ipynb             # Main analysis notebook
├── src/                       # Production package
│   ├── logger.py              # Logging utility
│   ├── data_collectors/       # Data collection modules
│   │   ├── market_data.py     # Market + sector data
│   │   ├── economic_data.py   # FRED indicators
│   │   ├── news_data.py       # Google News RSS
│   │   └── earnings_data.py   # Earnings sentiment
│   └── ai_agents/             # AI agent modules
│       ├── article_selector.py      # News curation
│       ├── polymarket_selector.py   # Prediction market curation
│       ├── sentiment_analyzer.py    # Sentiment analysis
│       └── market_analyzer.py       # Comprehensive synthesis
└── sentiment-sources.md       # Data sources documentation
```

---

## Output Examples

### Market Data with Sectors
```
📊 MAJOR INDICES:
🟢 S&P 500        : $ 6705.12 (+1.55%) [⚪ Last Close]
🟢 Nasdaq-100     : $  605.16 (+2.56%) [⚪ Last Close]
🔴 VIX            : $   20.52 (-12.42%) [⚪ Last Close]

📊 SECTOR PERFORMANCE (Ranked by Daily Change):
🟢 Technology             (XLK): +1.25% (day)  |  +2.85% (week)
🟢 Consumer Discretionary (XLY): +0.95% (day)  |  +2.10% (week)
...
🔴 Utilities              (XLU): -0.45% (day)  |  -0.80% (week)

Leader (Daily): Technology (+1.25%)
Laggard (Daily): Utilities (-0.45%)
```

### Polymarket Predictions (AI-Selected)
```
AI selected 10 most relevant prediction markets

1. Will 3 Fed rate cuts happen in 2025?
   Probability: 83.0%
   Relevance: Indicates likely easing, affecting borrowing and growth

2. US recession in 2025?
   Probability: 2.8%
   Relevance: Indicates contraction risk affecting GDP and jobs
   
[... 8 more economic predictions ...]
```

### AI Analysis
```
COMPREHENSIVE MARKET ANALYSIS
═══════════════════════════════════════════════════════

**Sector Rotation Analysis:**
The market is exhibiting clear risk-on behavior with Technology 
(+1.25%) and Consumer Discretionary (+0.95%) leading while defensive 
sectors lag. This rotation suggests investors are positioning for 
growth rather than protection...

**Fed Policy Assessment:**
Polymarket shows 83% probability of 3 rate cuts in 2025, combined 
with low recession probability (2.8%), indicating market expects 
soft landing scenario...

[... detailed comprehensive analysis ...]
```

---

## Features Deep Dive

### 1. Sector Rotation Analysis
Tracks all 11 S&P 500 sectors to identify:
- Risk-on vs. risk-off positioning
- Defensive vs. growth sentiment
- Inflation expectations (via Energy, Materials)
- Rate policy expectations (via Financials, Real Estate)

### 2. Polymarket Intelligence
- Fetches 500+ prediction markets from Gamma API
- **Pre-filters** to remove non-economic markets (sports, crypto tech, entertainment)
- **AI selects** 10-15 most relevant for Fed policy, recession, inflation
- **Deduplicates** repetitive series (e.g., keeps 2 Fed cut scenarios, not 9)

### 3. Multi-Agent AI Workflow
Each AI agent has a specialized role:
- **Article Selector**: Filters 30 articles → 12 most economically relevant
- **Polymarket Selector**: Filters 50 markets → 10 most important indicators
- **Sentiment Analyzer**: Analyzes selected articles for market impact
- **Market Analyzer**: Synthesizes all data sources into actionable insights

### 4. Configurable Logging
Control verbosity without code changes:
```python
LOG_LEVEL = "MINIMAL"  # Ultra-clean output
LOG_LEVEL = "NORMAL"   # Balanced (recommended)
LOG_LEVEL = "VERBOSE"  # Full debug info
```

---

## Dependencies

### Required
- `yfinance` - Market and sector data
- `requests` - HTTP requests for APIs
- `beautifulsoup4` - Web scraping
- `lxml` - XML/RSS parsing (Google News)
- `openai` - AI integration (compatible with Ollama)
- `pandas` - Data manipulation
- `pytz` - Timezone handling

### Optional
- `jupyter` - For running analysis notebook
- `ipykernel` - Jupyter kernel support

---

## Data Sources

### Market Data
- **Yahoo Finance API** (via yfinance) - Real-time/delayed market data
- **CNN** - Fear & Greed Index
- **Polymarket Gamma API** - Prediction markets

### Economic Data
- **Federal Reserve Economic Data (FRED)** - Economic indicators
  - Scraped from public web interface
  - Consider getting [free FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html) for production

### News
- **Google News RSS** - Aggregated news feeds
  - Provides titles, sources, descriptions
  - 7-day lookback window

---

## Performance

### Typical Runtime
- Market data collection: 3-5 seconds
- Sector data collection: 3-5 seconds
- Polymarket fetching + AI selection: 20-40 seconds
- Earnings sentiment: 5-10 seconds
- Economic indicators: 5-8 seconds
- News collection + AI analysis: 15-25 seconds
- Comprehensive AI analysis: 15-30 seconds

**Total: ~70-120 seconds** for complete analysis

### Optimization
- Data sources are fetched sequentially (can be parallelized)
- Polymarket selection optimized with 50-market limit
- Logging can be set to MINIMAL for faster output

---

## Troubleshooting

### yfinance Rate Limiting
**Symptom:** "Too many requests" errors  
**Solution:** Add delays between requests or cache results

### FRED Scraping Fails
**Symptom:** Economic indicators return None  
**Solution:** Get free [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html)

### Polymarket Returns No Markets
**Symptom:** "No economic markets found"  
**Reason:** All active markets may be closed/non-economic  
**Solution:** This is normal - analysis continues with other data sources

### AI Model Timeout
**Symptom:** Polymarket selection times out  
**Solution:** 
- Reduce `POLYMARKET_FILTER_LIMIT` in config.py
- Increase `AI_TIMEOUT_SECONDS`
- Use faster model

---

## Contributing

Contributions welcome! Areas for enhancement:

### High Priority
- Add bond market data (TLT, HYG, LQD)
- Add yield curve analysis (2Y-10Y spread)
- Add technical indicators (RSI, moving averages)
- Add market breadth indicators

### Medium Priority
- Add international markets (EEM, EFA)
- Add commodity tracking (GLD, USO)
- Add options data (put/call ratios)
- Add credit spreads

### Nice to Have
- Async data collection
- Data caching layer
- Automated testing
- Database storage

---

## License

MIT License - See repository root

---

## Acknowledgments

- Built for the LLM Engineering bootcamp
- Uses Ollama for local AI inference
- Data provided by Yahoo Finance, FRED, CNN, Polymarket, Google News

---

## Version History

### v1.0 (Current)
- ✅ Multi-agent AI workflow
- ✅ Comprehensive sector tracking (11 sectors)
- ✅ Intelligent Polymarket filtering
- ✅ Automatic deduplication
- ✅ Configurable logging
- ✅ Production-ready architecture

---


