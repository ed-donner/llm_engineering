# ARIA — Automated Real-time Investment Alert Agent

Multi-agent pipeline that monitors commodities, stocks, indices, and crypto; runs technical and sentiment analysis; and sends Pushover alerts when opportunities meet the score threshold.

## Agents

1. **DATA_FETCHER** — Fetches prices and OHLCV from Alpha Vantage (stocks/indices), Metals-API (gold/silver), CoinGecko (crypto).
2. **TECH_ANALYST** — RSI, MACD, Bollinger Bands, EMA cross; scores each asset and assigns a bias (STRONG BUY … STRONG SELL).
3. **SENTIMENT_AGENT** — NewsAPI headlines + LLM (via LiteLLM) for sentiment and a one-sentence narrative.
4. **DECISION_AGENT** — Combines tech and sentiment into a final score; applies alert threshold, cooldowns, and market-hours rules.
5. **NOTIFIER** — Sends formatted Pushover push notifications for assets that qualify.

## Setup

```bash
cd week8/community_contributions/chrys
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys (Pushover, Alpha Vantage, Metals-API, NewsAPI, OpenAI).
```

## Run

- **Gradio UI** (agent-colored log + results table):
  ```bash
  python app.py
  ```
- **CLI one-off run:**
  ```bash
  python main.py run-once
  ```
- **Background scheduler** (30 min interval):
  ```bash
  python main.py schedule
  ```

## Config

- Watchlist: default list in `config.py`; override with `ARIA_WATCHLIST` (comma-separated).
- Alert threshold: 65+ final score; max 3 alerts/hour; 2-hour cooldown per asset.
- Outside US market hours (9am–5pm ET), only 24/7 assets (crypto, gold, silver, oil) can trigger alerts.

## Audit log

Runs are logged to `data/aria_audit.db` (SQLite). Optional: purge rows older than 90 days (see `db.purge_older_than_days()`).
