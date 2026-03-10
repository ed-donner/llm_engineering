# AI Economy Sentiment Agent

**AI-powered market intelligence with multi-agent workflow**

Repository URL: https://github.com/brianschroeder/ai-economy-sentiment-agent

## What It Does
Analyzes market sentiment by synthesizing data from 6 sources: market prices, sectors, economic indicators, prediction markets, earnings, and news.

# Multi-Agent AI Workflow
Agent 1: Curates most relevant news articles (12 from 30+)
Agent 2: Selects most relevant Polymarket predictions (10-15 from 50+)
Agent 3: Analyzes sentiment of selected articles
Agent 4: Synthesizes comprehensive market analysis

## Key Features
- ✅ **Comprehensive coverage**: 14 market assets (3 indices + 11 sectors)
- 🤖 **Multi-agent AI**: 4 specialized agents (curation → sentiment → synthesis)
- 🎯 **Smart filtering**: Removes sports/crypto/entertainment from predictions
- 🔄 **Auto-dedup**: Reduces repetitive prediction series
- 🎚️ **Configurable**: MINIMAL/NORMAL/VERBOSE logging modes

## Architecture
Clean modular package: `config.py` + `src/data_collectors/` + `src/ai_agents/` + `analysis.ipynb`

**Stack**: Python 3.11, yfinance, beautifulsoup4, openai (Ollama), pandas, pytz

## Technical Highlights

**Sector Tracking**: 3 indices → 14 assets (adds 11 S&P sectors) for rotation analysis  
**Smart Filtering**: Triple-layer system removes 99%+ non-economic predictions  
**Logging**: MINIMAL/NORMAL/VERBOSE modes via config  
**Architecture**: Modular package structure (not monolithic notebook)

## Sample Output
```
📊 MAJOR INDICES & SECTORS (with % changes)
Polymarket: 10 AI-selected economic predictions with probabilities
AI Analysis: Risk-on behavior detected; Tech leading, defensives lagging;
             83% probability 3 Fed cuts → soft landing expectations
```

## Quick Start
```bash
pip install -r requirements.txt
ollama serve  # Start Ollama
jupyter notebook analysis.ipynb
```
**Runtime**: ~70-120 seconds | **Dependencies**: See `requirements.txt`

## Testing
✅ End-to-end tested with all data sources and edge cases

## Documentation
Full README.md with setup guide, usage examples, troubleshooting

---

**Type**: New Feature | **Lines**: ~2000+ | **Breaking Changes**: None
