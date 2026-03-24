"""ARIA orchestrator: run all agents in sequence and pass state."""
from typing import List, Tuple

from config import get_watchlist, ALERT_SCORE_THRESHOLD, PUSHOVER_USER, PUSHOVER_TOKEN
from models import AssetData, TechResult, SentimentResult, DecisionRecord
from agents import DataFetcherAgent, TechAnalystAgent, SentimentAgent, DecisionAgent, NotifierAgent
from db import log_decisions

from config import (
    ALPHA_VANTAGE_API_KEY,
    COMMODITY_PRICE_API_KEY,
    NEWSAPI_KEY,
    OPENROUTER_API_KEY,
    SENTIMENT_MODEL,
)


def run_pipeline() -> Tuple[List[DecisionRecord], List[AssetData]]:
    watchlist = get_watchlist()
    # 1. Data Fetcher
    fetcher = DataFetcherAgent(alpha_key=ALPHA_VANTAGE_API_KEY, metals_key=COMMODITY_PRICE_API_KEY)
    asset_data = fetcher.run(watchlist)
    if not asset_data:
        return [], []

    # 2. Tech Analyst
    tech_agent = TechAnalystAgent()
    tech_results = tech_agent.run(asset_data)

    # 3. Sentiment (only for non-neutral)
    assets_for_sentiment = [tr.asset for tr in tech_results if tr.bias != "NEUTRAL"]
    sentiment_agent = SentimentAgent(
        newsapi_key=NEWSAPI_KEY,
        model=SENTIMENT_MODEL,
        openrouter_key=OPENROUTER_API_KEY,
    )
    sentiment_results = sentiment_agent.run(tech_results, assets_for_sentiment)
    sentiment_by_asset = {s.asset: s for s in sentiment_results}
    asset_by_asset = {a.asset: a for a in asset_data}

    # 4. Decision Agent
    decision_agent = DecisionAgent()
    records = decision_agent.run(tech_results, sentiment_results, asset_data)

    # 5. Notifier: only ALERT, top 1-2 by score, up to MAX per hour (handled in decision)
    alert_records = [r for r in records if r.decision == "ALERT"]
    alert_records.sort(key=lambda x: x.final_score, reverse=True)
    to_send = alert_records[:2]  # Top 2
    notifier = NotifierAgent(user=PUSHOVER_USER, token=PUSHOVER_TOKEN)
    to_send_tuples: List[Tuple[DecisionRecord, TechResult, SentimentResult | None, AssetData | None]] = []
    tech_by_asset = {t.asset: t for t in tech_results}
    for rec in to_send:
        tech = tech_by_asset[rec.asset]
        sent = sentiment_by_asset.get(rec.asset)
        ad = asset_by_asset.get(rec.asset)
        to_send_tuples.append((rec, tech, sent, ad))
    notifier.run(to_send_tuples)

    # Audit log
    log_decisions(records)
    return records, asset_data
