"""Reddit data collection service using PRAW."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

import praw
from praw.models import Comment, Submission

from .utils import (
    NormalizedItem,
    ServiceError,
    ServiceWarning,
    ensure_timezone,
    sanitize_text,
)


TIME_FILTER_MAP = {
    "24h": "day",
    "7d": "week",
    "30d": "month",
}


def _iter_submissions(subreddit: praw.models.Subreddit, query: str, limit: int, time_filter: str) -> Iterable[Submission]:
    return subreddit.search(query=query, sort="new", time_filter=time_filter, limit=limit * 3)


def _iter_comments(submission: Submission) -> Iterable[Comment]:
    submission.comments.replace_more(limit=0)
    return submission.comments.list()


def _normalize_submission(submission: Submission) -> NormalizedItem:
    created = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
    return NormalizedItem(
        source="reddit",
        id=submission.id,
        url=f"https://www.reddit.com{submission.permalink}",
        author=str(submission.author) if submission.author else None,
        timestamp=ensure_timezone(created),
        text=f"{submission.title}\n\n{submission.selftext or ''}",
        meta={
            "score": submission.score,
            "num_comments": submission.num_comments,
            "subreddit": submission.subreddit.display_name,
            "type": "submission",
        },
    )


def _normalize_comment(comment: Comment, submission: Submission) -> NormalizedItem:
    created = datetime.fromtimestamp(comment.created_utc, tz=timezone.utc)
    return NormalizedItem(
        source="reddit",
        id=comment.id,
        url=f"https://www.reddit.com{comment.permalink}",
        author=str(comment.author) if comment.author else None,
        timestamp=ensure_timezone(created),
        text=comment.body,
        meta={
            "score": comment.score,
            "subreddit": submission.subreddit.display_name,
            "type": "comment",
            "submission_title": submission.title,
        },
    )


def fetch_mentions(
    brand: str,
    credentials: Dict[str, str],
    limit: int = 25,
    date_filter: str = "7d",
    min_upvotes: int = 0,
) -> List[NormalizedItem]:
    """Fetch recent Reddit submissions/comments mentioning the brand."""
    client_id = credentials.get("client_id")
    client_secret = credentials.get("client_secret")
    user_agent = credentials.get("user_agent")

    if not all([client_id, client_secret, user_agent]):
        raise ServiceWarning("Reddit credentials are missing. Provide them in the sidebar to enable this source.")

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        reddit.read_only = True
    except Exception as exc:  # noqa: BLE001
        raise ServiceError(f"Failed to initialize Reddit client: {exc}") from exc

    time_filter = TIME_FILTER_MAP.get(date_filter.lower(), "week")
    subreddit = reddit.subreddit("all")
    results: List[NormalizedItem] = []
    seen_ids: set[str] = set()
    try:
        for submission in _iter_submissions(subreddit, query=brand, limit=limit, time_filter=time_filter):
            if submission.id in seen_ids:
                continue
            if submission.score < min_upvotes:
                continue
            normalized_submission = _normalize_submission(submission)
            normalized_submission["text"] = sanitize_text(normalized_submission["text"])
            if normalized_submission["text"]:
                results.append(normalized_submission)
                seen_ids.add(submission.id)
            if len(results) >= limit:
                break

            # Fetch comments mentioning the brand
            match_count = 0
            for comment in _iter_comments(submission):
                if brand.lower() not in (comment.body or "").lower():
                    continue
                if comment.score < min_upvotes:
                    continue
                normalized_comment = _normalize_comment(comment, submission)
                normalized_comment["text"] = sanitize_text(normalized_comment["text"])
                if not normalized_comment["text"]:
                    continue
                if normalized_comment["id"] in seen_ids:
                    continue
                results.append(normalized_comment)
                seen_ids.add(normalized_comment["id"])
                match_count += 1
                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break
            # Respect rate limits
            if match_count:
                time.sleep(1)
    except Exception as exc:  # noqa: BLE001
        raise ServiceError(f"Error while fetching Reddit data: {exc}") from exc
    return results
