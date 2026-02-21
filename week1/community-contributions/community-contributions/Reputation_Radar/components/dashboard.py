"""Render the ReputationRadar dashboard components."""

from __future__ import annotations

from typing import Dict, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

SOURCE_CHIPS = {
    "reddit": "🔺 Reddit",
    "twitter": "✖️ Twitter",
    "trustpilot": "⭐ Trustpilot",
}

SENTIMENT_COLORS = {
    "positive": "#4caf50",
    "neutral": "#90a4ae",
    "negative": "#ef5350",
}


def render_overview(df: pd.DataFrame) -> None:
    """Display charts summarising sentiment."""
    counts = (
        df["label"]
        .value_counts()
        .reindex(["positive", "neutral", "negative"], fill_value=0)
        .rename_axis("label")
        .reset_index(name="count")
    )
    pie = px.pie(
        counts,
        names="label",
        values="count",
        color="label",
        color_discrete_map=SENTIMENT_COLORS,
        title="Sentiment distribution",
    )
    pie.update_traces(textinfo="percent+label")

    ts = (
        df.set_index("timestamp")
        .groupby([pd.Grouper(freq="D"), "label"])
        .size()
        .reset_index(name="count")
    )
    if not ts.empty:
        ts_plot = px.line(
            ts,
            x="timestamp",
            y="count",
            color="label",
            color_discrete_map=SENTIMENT_COLORS,
            markers=True,
            title="Mentions over time",
        )
    else:
        ts_plot = None

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(pie, use_container_width=True)
    with col2:
        if ts_plot is not None:
            st.plotly_chart(ts_plot, use_container_width=True)
        else:
            st.info("Not enough data for a time-series. Try widening the date range.", icon="📆")


def render_top_comments(df: pd.DataFrame) -> None:
    """Show representative comments per sentiment."""
    st.subheader("Representative Mentions")
    cols = st.columns(3)
    for idx, sentiment in enumerate(["positive", "neutral", "negative"]):
        subset = (
            df[df["label"] == sentiment]
            .sort_values("confidence", ascending=False)
            .head(5)
        )
        with cols[idx]:
            st.caption(sentiment.capitalize())
            if subset.empty:
                st.write("No items yet.")
                continue
            for _, row in subset.iterrows():
                chip = SOURCE_CHIPS.get(row["source"], row["source"])
                author = row.get("author") or "Unknown"
                timestamp = row["timestamp"].strftime("%Y-%m-%d %H:%M")
                label = f"{chip} · {author} · {timestamp}"
                if row.get("url"):
                    st.markdown(f"- [{label}]({row['url']})")
                else:
                    st.markdown(f"- {label}")


def render_source_explorer(df: pd.DataFrame) -> None:
    """Interactive tabular explorer with pagination and filters."""
    with st.expander("Source Explorer", expanded=False):
        search_term = st.text_input("Search mentions", key="explorer_search")
        selected_source = st.selectbox("Source filter", options=["All"] + list(SOURCE_CHIPS.values()))
        min_conf = st.slider("Minimum confidence", min_value=0.0, max_value=1.0, value=0.0, step=0.1)

        filtered = df.copy()
        if search_term:
            filtered = filtered[filtered["text"].str.contains(search_term, case=False, na=False)]
        if selected_source != "All":
            source_key = _reverse_lookup(selected_source)
            if source_key:
                filtered = filtered[filtered["source"] == source_key]
        filtered = filtered[filtered["confidence"] >= min_conf]

        if filtered.empty:
            st.info("No results found. Try widening the date range or removing filters.", icon="🪄")
            return

        page_size = 10
        total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
        start = (page - 1) * page_size
        end = start + page_size

        explorer_df = filtered.iloc[start:end].copy()
        explorer_df["source"] = explorer_df["source"].map(SOURCE_CHIPS).fillna(explorer_df["source"])
        explorer_df["timestamp"] = explorer_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
        explorer_df = explorer_df[["timestamp", "source", "author", "label", "confidence", "text", "url"]]

        st.dataframe(explorer_df, use_container_width=True, hide_index=True)


def _reverse_lookup(value: str) -> Optional[str]:
    for key, chip in SOURCE_CHIPS.items():
        if chip == value:
            return key
    return None
