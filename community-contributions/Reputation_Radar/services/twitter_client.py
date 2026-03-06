"""Twitter (X) data collection using the v2 recent search API."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests

from .utils import NormalizedItem, ServiceError, ServiceWarning, ensure_timezone, sanitize_text

SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"


def _build_query(brand: str, language: str) -> str:
    terms = [brand]
    if language:
        terms.append(f"lang:{language}")
    return " ".join(terms)


def fetch_mentions(
    brand: str,
    bearer_token: Optional[str],
    limit: int = 25,
    min_likes: int = 0,
    language: str = "en",
) -> List[NormalizedItem]:
    """Fetch recent tweets mentioning the brand."""
    if not bearer_token:
        raise ServiceWarning(
            "Twitter bearer token not provided. Add it in the sidebar to enable Twitter ingestion."
        )

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "ReputationRadar/1.0",
    }
    params = {
        "query": _build_query(brand, language),
        "max_results": min(100, limit),
        "tweet.fields": "author_id,created_at,lang,public_metrics",
        "expansions": "author_id",
        "user.fields": "name,username",
    }

    collected: List[NormalizedItem] = []
    next_token: Optional[str] = None

    while len(collected) < limit:
        if next_token:
            params["next_token"] = next_token
        response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=15)
        if response.status_code == 401:
            raise ServiceWarning("Twitter API authentication failed. Please verify the bearer token.")
        if response.status_code == 429:
            time.sleep(5)
            continue
        if response.status_code >= 400:
            raise ServiceError(f"Twitter API error {response.status_code}: {response.text}")

        payload = response.json()
        data = payload.get("data", [])
        includes = payload.get("includes", {})
        users_index = {user["id"]: user for user in includes.get("users", [])}

        for tweet in data:
            created_at = datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00"))
            author_info = users_index.get(tweet["author_id"], {})
            item = NormalizedItem(
                source="twitter",
                id=tweet["id"],
                url=f"https://twitter.com/{author_info.get('username','')}/status/{tweet['id']}",
                author=author_info.get("username"),
                timestamp=ensure_timezone(created_at),
                text=sanitize_text(tweet["text"]),
                meta={
                    "likes": tweet.get("public_metrics", {}).get("like_count", 0),
                    "retweets": tweet.get("public_metrics", {}).get("retweet_count", 0),
                    "replies": tweet.get("public_metrics", {}).get("reply_count", 0),
                    "quote_count": tweet.get("public_metrics", {}).get("quote_count", 0),
                },
            )
            if not item["text"]:
                continue
            if item["meta"]["likes"] < min_likes:
                continue
            collected.append(item)
            if len(collected) >= limit:
                break

        next_token = payload.get("meta", {}).get("next_token")
        if not next_token:
            break
        time.sleep(1)  # stay friendly to rate limits

    return collected[:limit]
