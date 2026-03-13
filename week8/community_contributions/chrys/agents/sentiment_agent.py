"""SENTIMENT_AGENT: fetch news and score sentiment via LLM."""
import json
import os
from typing import List

import requests
from agents.base import AgentBase
from models import SentimentResult, TechResult

NEWS_API_URL = "https://newsapi.org/v2/everything"


def _fetch_news(asset: str, api_key: str, max_articles: int = 5) -> List[str]:
    if not api_key:
        return []
    try:
        # Map symbol to search term
        q = asset.replace("/", " ").replace("USD", "") + " market"
        r = requests.get(
            NEWS_API_URL,
            params={
                "q": q,
                "apiKey": api_key,
                "sortBy": "publishedAt",
                "pageSize": max_articles,
                "language": "en",
            },
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        articles = data.get("articles", [])[:max_articles]
        return [a.get("title", "") for a in articles if a.get("title")]
    except Exception:
        return []


def _llm_sentiment(headlines: List[str], model: str, api_key: str = "") -> tuple[str, int, str]:
    if not headlines:
        return "MIXED", 0, "No headlines available."
    try:
        from litellm import completion
        prompt = (
            "Given these news headlines about a financial asset, determine the dominant sentiment.\n"
            "Reply with exactly this JSON (no markdown): {\"sentiment\": \"POSITIVE\" or \"NEGATIVE\" or \"MIXED\", "
            "\"sentiment_score\": 1 or 0 or -1, \"narrative\": \"one short sentence summarizing the key narrative\"}\n\n"
            "Headlines:\n" + "\n".join(f"- {h}" for h in headlines[:5])
        )
        kwargs = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        if api_key and model.startswith("openrouter/"):
            kwargs["api_key"] = api_key
        resp = completion(**kwargs)
        text = resp.choices[0].message.content.strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        data = json.loads(text)
        sent = data.get("sentiment", "MIXED").upper()
        if "POSITIVE" in sent:
            sent, score = "POSITIVE", 1
        elif "NEGATIVE" in sent:
            sent, score = "NEGATIVE", -1
        else:
            sent, score = "MIXED", 0
        narrative = data.get("narrative", "")[:200]
        return sent, score, narrative
    except Exception:
        return "MIXED", 0, "Sentiment could not be determined."


class SentimentAgent(AgentBase):
    name = "SENTIMENT_AGENT"
    logger_name = "aria.sentiment_agent"

    def __init__(self, newsapi_key: str = "", model: str = "openrouter/openai/gpt-5-nano", openrouter_key: str = ""):
        super().__init__()
        self.newsapi_key = newsapi_key or os.getenv("NEWSAPI_KEY", "")
        self.model = model
        self.openrouter_key = openrouter_key or os.getenv("OPENROUTER_API_KEY", "")

    def run(self, tech_results: List[TechResult], assets_for_sentiment: List[str]) -> List[SentimentResult]:
        self.log("Running sentiment analysis for non-neutral assets")
        results: List[SentimentResult] = []
        for tr in tech_results:
            if tr.asset not in assets_for_sentiment:
                continue
            headlines = _fetch_news(tr.asset, self.newsapi_key)
            sentiment, score, narrative = _llm_sentiment(headlines, self.model, self.openrouter_key)
            results.append(SentimentResult(
                asset=tr.asset,
                headlines=headlines,
                sentiment=sentiment,
                sentiment_score=score,
                narrative=narrative,
            ))
            self.log(f"{tr.asset}: {sentiment} (score={score})")
        self.log(f"Sentiment complete: {len(results)} assets")
        return results
