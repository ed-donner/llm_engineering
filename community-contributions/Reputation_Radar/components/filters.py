"""Sidebar filters and configuration controls."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import streamlit as st

DATE_RANGE_LABELS = {
    "24h": "Last 24 hours",
    "7d": "Last 7 days",
    "30d": "Last 30 days",
}

SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "de": "German",
    "fr": "French",
}


def _store_secret(key: str, value: str) -> None:
    """Persist sensitive values in session state only."""
    if value:
        st.session_state.setdefault("secrets", {})
        st.session_state["secrets"][key] = value


def _get_secret(key: str, default: str = "") -> str:
    return st.session_state.get("secrets", {}).get(key, default)


def render_sidebar(env_defaults: Dict[str, Optional[str]], openai_notices: Tuple[str, ...]) -> Dict[str, object]:
    """Render all sidebar controls and return configuration."""
    with st.sidebar:
        st.header("Tune Your Radar", anchor=False)
        brand = st.text_input("Brand Name*", value=st.session_state.get("brand_input", ""))
        if brand:
            st.session_state["brand_input"] = brand

        date_range = st.selectbox(
            "Date Range",
            options=list(DATE_RANGE_LABELS.keys()),
            format_func=lambda key: DATE_RANGE_LABELS[key],
            index=1,
        )
        min_reddit_upvotes = st.number_input(
            "Minimum Reddit upvotes",
            min_value=0,
            value=st.session_state.get("min_reddit_upvotes", 4),
        )
        st.session_state["min_reddit_upvotes"] = min_reddit_upvotes
        min_twitter_likes = st.number_input(
            "Minimum X likes",
            min_value=0,
            value=st.session_state.get("min_twitter_likes", 100),
        )
        st.session_state["min_twitter_likes"] = min_twitter_likes
        language = st.selectbox(
            "Language",
            options=list(SUPPORTED_LANGUAGES.keys()),
            format_func=lambda key: SUPPORTED_LANGUAGES[key],
            index=0,
        )

        st.markdown("### Sources")
        reddit_enabled = st.toggle("🔺 Reddit", value=st.session_state.get("reddit_enabled", True))
        twitter_enabled = st.toggle("✖️ Twitter", value=st.session_state.get("twitter_enabled", True))
        trustpilot_enabled = st.toggle("⭐ Trustpilot", value=st.session_state.get("trustpilot_enabled", True))
        st.session_state["reddit_enabled"] = reddit_enabled
        st.session_state["twitter_enabled"] = twitter_enabled
        st.session_state["trustpilot_enabled"] = trustpilot_enabled

        st.markdown("### API Keys")
        openai_key_default = env_defaults.get("OPENAI_API_KEY") or _get_secret("OPENAI_API_KEY")
        openai_key = st.text_input("OpenAI API Key", value=openai_key_default or "", type="password", help="Stored only in this session.")
        _store_secret("OPENAI_API_KEY", openai_key.strip())
        reddit_client_id = st.text_input("Reddit Client ID", value=env_defaults.get("REDDIT_CLIENT_ID") or _get_secret("REDDIT_CLIENT_ID"), type="password")
        reddit_client_secret = st.text_input("Reddit Client Secret", value=env_defaults.get("REDDIT_CLIENT_SECRET") or _get_secret("REDDIT_CLIENT_SECRET"), type="password")
        reddit_user_agent = st.text_input("Reddit User Agent", value=env_defaults.get("REDDIT_USER_AGENT") or _get_secret("REDDIT_USER_AGENT"))
        twitter_bearer_token = st.text_input("Twitter Bearer Token", value=env_defaults.get("TWITTER_BEARER_TOKEN") or _get_secret("TWITTER_BEARER_TOKEN"), type="password")
        _store_secret("REDDIT_CLIENT_ID", reddit_client_id.strip())
        _store_secret("REDDIT_CLIENT_SECRET", reddit_client_secret.strip())
        _store_secret("REDDIT_USER_AGENT", reddit_user_agent.strip())
        _store_secret("TWITTER_BEARER_TOKEN", twitter_bearer_token.strip())

        if openai_notices:
            for notice in openai_notices:
                st.info(notice)

        with st.expander("Advanced Options", expanded=False):
            reddit_limit = st.slider("Reddit results", min_value=10, max_value=100, value=st.session_state.get("reddit_limit", 40), step=5)
            twitter_limit = st.slider("Twitter results", min_value=10, max_value=100, value=st.session_state.get("twitter_limit", 40), step=5)
            trustpilot_limit = st.slider("Trustpilot results", min_value=10, max_value=60, value=st.session_state.get("trustpilot_limit", 30), step=5)
            llm_batch_size = st.slider("OpenAI batch size", min_value=5, max_value=20, value=st.session_state.get("llm_batch_size", 20), step=5)
            st.session_state["reddit_limit"] = reddit_limit
            st.session_state["twitter_limit"] = twitter_limit
            st.session_state["trustpilot_limit"] = trustpilot_limit
            st.session_state["llm_batch_size"] = llm_batch_size

    return {
        "brand": brand.strip(),
        "date_range": date_range,
        "min_reddit_upvotes": min_reddit_upvotes,
        "min_twitter_likes": min_twitter_likes,
        "language": language,
        "sources": {
            "reddit": reddit_enabled,
            "twitter": twitter_enabled,
            "trustpilot": trustpilot_enabled,
        },
        "limits": {
            "reddit": reddit_limit,
            "twitter": twitter_limit,
            "trustpilot": trustpilot_limit,
        },
        "batch_size": llm_batch_size,
        "credentials": {
            "openai": openai_key.strip(),
            "reddit": {
                "client_id": reddit_client_id.strip(),
                "client_secret": reddit_client_secret.strip(),
                "user_agent": reddit_user_agent.strip(),
            },
            "twitter": twitter_bearer_token.strip(),
        },
    }
