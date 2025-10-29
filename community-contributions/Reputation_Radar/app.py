"""ReputationRadar Streamlit application entrypoint."""

from __future__ import annotations

import io
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from components.dashboard import render_overview, render_source_explorer, render_top_comments
from components.filters import render_sidebar
from components.summary import render_summary
from components.loaders import show_empty_state, source_status
from services import llm, reddit_client, trustpilot_scraper, twitter_client, utils
from services.llm import SentimentResult
from services.utils import (
    NormalizedItem,
    ServiceError,
    ServiceWarning,
    initialize_logger,
    load_sample_items,
    normalize_items,
    parse_date_range,
    validate_openai_key,
)


st.set_page_config(page_title="ReputationRadar", page_icon="📡", layout="wide")
load_dotenv(override=True)
LOGGER = initialize_logger()

st.title("📡 ReputationRadar")
st.caption("Aggregate brand chatter, classify sentiment, and surface actionable insights in minutes.")


def _get_env_defaults() -> Dict[str, Optional[str]]:
    """Read supported credentials from environment variables."""
    return {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "REDDIT_CLIENT_ID": os.getenv("REDDIT_CLIENT_ID"),
        "REDDIT_CLIENT_SECRET": os.getenv("REDDIT_CLIENT_SECRET"),
        "REDDIT_USER_AGENT": os.getenv("REDDIT_USER_AGENT", "ReputationRadar/1.0"),
        "TWITTER_BEARER_TOKEN": os.getenv("TWITTER_BEARER_TOKEN"),
    }


@st.cache_data(ttl=600, show_spinner=False)
def cached_reddit_fetch(
    brand: str,
    limit: int,
    date_range: str,
    min_upvotes: int,
    client_id: str,
    client_secret: str,
    user_agent: str,
) -> List[NormalizedItem]:
    credentials = {
        "client_id": client_id,
        "client_secret": client_secret,
        "user_agent": user_agent,
    }
    return reddit_client.fetch_mentions(
        brand=brand,
        credentials=credentials,
        limit=limit,
        date_filter=date_range,
        min_upvotes=min_upvotes,
    )


@st.cache_data(ttl=600, show_spinner=False)
def cached_twitter_fetch(
    brand: str,
    limit: int,
    min_likes: int,
    language: str,
    bearer: str,
) -> List[NormalizedItem]:
    return twitter_client.fetch_mentions(
        brand=brand,
        bearer_token=bearer,
        limit=limit,
        min_likes=min_likes,
        language=language,
    )


@st.cache_data(ttl=600, show_spinner=False)
def cached_trustpilot_fetch(
    brand: str,
    language: str,
    pages: int = 2,
) -> List[NormalizedItem]:
    return trustpilot_scraper.fetch_reviews(brand=brand, language=language, pages=pages)


def _to_dataframe(items: List[NormalizedItem], sentiments: List[SentimentResult]) -> pd.DataFrame:
    data = []
    for item, sentiment in zip(items, sentiments):
        data.append(
            {
                "source": item["source"],
                "id": item["id"],
                "url": item.get("url"),
                "author": item.get("author"),
                "timestamp": item["timestamp"],
                "text": item["text"],
                "label": sentiment.label,
                "confidence": sentiment.confidence,
                "meta": json.dumps(item.get("meta", {})),
            }
        )
    df = pd.DataFrame(data)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def _build_pdf(summary: Optional[Dict[str, str]], df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=60,
        bottomMargin=40,
        title="ReputationRadar Executive Summary",
    )
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        textColor="#555555",
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        leading=14,
        fontSize=11,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=body_style,
        leftIndent=16,
        bulletIndent=8,
        spaceBefore=2,
        spaceAfter=2,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading3"],
        spaceBefore=10,
        spaceAfter=6,
    )

    story: List[Paragraph | Spacer | Table] = []
    story.append(Paragraph("ReputationRadar Executive Summary", title_style))
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 18))

    if summary and summary.get("raw"):
        story.extend(_summary_to_story(summary["raw"], body_style, bullet_style, heading_style))
    else:
        story.append(
            Paragraph(
                "Executive summary disabled (OpenAI key missing).",
                body_style,
            )
        )
    story.append(Spacer(1, 16))
    story.append(Paragraph("Sentiment Snapshot", styles["Heading2"]))
    story.append(Spacer(1, 10))

    table_data: List[List[Paragraph]] = [
        [
            Paragraph("Date", body_style),
            Paragraph("Sentiment", body_style),
            Paragraph("Source", body_style),
            Paragraph("Excerpt", body_style),
        ]
    ]
    snapshot = df.sort_values("timestamp", ascending=False).head(15)
    for _, row in snapshot.iterrows():
        excerpt = _truncate_text(row["text"], 180)
        table_data.append(
            [
                Paragraph(row["timestamp"].strftime("%Y-%m-%d %H:%M"), body_style),
                Paragraph(row["label"].title(), body_style),
                Paragraph(row["source"].title(), body_style),
                Paragraph(excerpt, body_style),
            ]
        )

    table = Table(table_data, colWidths=[90, 70, 80, 250])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#9ca3af")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
            ]
        )
    )
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def _summary_to_story(
    raw_summary: str,
    body_style: ParagraphStyle,
    bullet_style: ParagraphStyle,
    heading_style: ParagraphStyle,
) -> List[Paragraph | Spacer]:
    story: List[Paragraph | Spacer] = []
    lines = [line.strip() for line in raw_summary.splitlines()]
    for line in lines:
        if not line:
            continue
        clean = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        if clean.endswith(":") and len(clean) < 40:
            story.append(Paragraph(clean.rstrip(":"), heading_style))
            continue
        if clean.lower().startswith(("highlights", "risks & concerns", "recommended actions", "overall tone")):
            story.append(Paragraph(clean, heading_style))
            continue
        if line.startswith(("-", "*")):
            bullet_text = re.sub(r"\*\*(.*?)\*\*", r"\1", line[1:].strip())
            story.append(Paragraph(bullet_text, bullet_style, bulletText="•"))
        else:
            story.append(Paragraph(clean, body_style))
    story.append(Spacer(1, 10))
    return story


def _truncate_text(text: str, max_length: int) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= max_length:
        return clean
    return clean[: max_length - 1].rstrip() + "…"


def _build_excel(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    export_df = df.copy()
    export_df["timestamp"] = export_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Mentions")
        worksheet = writer.sheets["Mentions"]
        for idx, column in enumerate(export_df.columns):
            series = export_df[column].astype(str)
            max_len = min(60, max(series.map(len).max(), len(column)) + 2)
            worksheet.set_column(idx, idx, max_len)
    buffer.seek(0)
    return buffer.getvalue()


def main() -> None:
    env_defaults = _get_env_defaults()
    openai_env_key = env_defaults.get("OPENAI_API_KEY") or st.session_state.get("secrets", {}).get("OPENAI_API_KEY")
    validated_env_key, notices = validate_openai_key(openai_env_key)
    config = render_sidebar(env_defaults, tuple(notices))

    chosen_key = config["credentials"]["openai"] or validated_env_key
    openai_key, runtime_notices = validate_openai_key(chosen_key)
    for msg in runtime_notices:
        st.sidebar.info(msg)

    run_clicked = st.button("Run Analysis 🚀", type="primary")

    if not run_clicked:
        show_empty_state("Enter a brand name and click **Run Analysis** to get started.")
        return

    if not config["brand"]:
        st.error("Brand name is required.")
        return

    threshold = parse_date_range(config["date_range"])
    collected: List[NormalizedItem] = []

    with st.container():
        if config["sources"]["reddit"]:
            with source_status("Fetching Reddit mentions") as status:
                try:
                    reddit_items = cached_reddit_fetch(
                        brand=config["brand"],
                        limit=config["limits"]["reddit"],
                        date_range=config["date_range"],
                        min_upvotes=config["min_reddit_upvotes"],
                        client_id=config["credentials"]["reddit"]["client_id"],
                        client_secret=config["credentials"]["reddit"]["client_secret"],
                        user_agent=config["credentials"]["reddit"]["user_agent"],
                    )
                    reddit_items = [item for item in reddit_items if item["timestamp"] >= threshold]
                    status.write(f"Fetched {len(reddit_items)} Reddit items.")
                    collected.extend(reddit_items)
                except ServiceWarning as warning:
                    st.warning(str(warning))
                    demo = load_sample_items("reddit_sample")
                    if demo:
                        st.info("Loaded demo Reddit data.", icon="🧪")
                        collected.extend(demo)
                except ServiceError as error:
                    st.error(f"Reddit fetch failed: {error}")
        if config["sources"]["twitter"]:
            with source_status("Fetching Twitter mentions") as status:
                try:
                    twitter_items = cached_twitter_fetch(
                        brand=config["brand"],
                        limit=config["limits"]["twitter"],
                        min_likes=config["min_twitter_likes"],
                        language=config["language"],
                        bearer=config["credentials"]["twitter"],
                    )
                    twitter_items = [item for item in twitter_items if item["timestamp"] >= threshold]
                    status.write(f"Fetched {len(twitter_items)} tweets.")
                    collected.extend(twitter_items)
                except ServiceWarning as warning:
                    st.warning(str(warning))
                    demo = load_sample_items("twitter_sample")
                    if demo:
                        st.info("Loaded demo Twitter data.", icon="🧪")
                        collected.extend(demo)
                except ServiceError as error:
                    st.error(f"Twitter fetch failed: {error}")
        if config["sources"]["trustpilot"]:
            with source_status("Fetching Trustpilot reviews") as status:
                try:
                    trustpilot_items = cached_trustpilot_fetch(
                        brand=config["brand"],
                        language=config["language"],
                    )
                    trustpilot_items = [item for item in trustpilot_items if item["timestamp"] >= threshold]
                    status.write(f"Fetched {len(trustpilot_items)} reviews.")
                    collected.extend(trustpilot_items)
                except ServiceWarning as warning:
                    st.warning(str(warning))
                    demo = load_sample_items("trustpilot_sample")
                    if demo:
                        st.info("Loaded demo Trustpilot data.", icon="🧪")
                        collected.extend(demo)
                except ServiceError as error:
                    st.error(f"Trustpilot fetch failed: {error}")

    if not collected:
        show_empty_state("No mentions found. Try enabling more sources or loosening filters.")
        return

    cleaned = normalize_items(collected)
    if not cleaned:
        show_empty_state("All results were filtered out as noise. Try again with different settings.")
        return

    sentiment_service = llm.LLMService(
        api_key=config["credentials"]["openai"] or openai_key,
        batch_size=config["batch_size"],
    )
    sentiments = sentiment_service.classify_sentiment_batch([item["text"] for item in cleaned])
    df = _to_dataframe(cleaned, sentiments)

    render_overview(df)
    render_top_comments(df)

    summary_payload: Optional[Dict[str, str]] = None
    if sentiment_service.available():
        try:
            summary_payload = sentiment_service.summarize_overall(
                [{"label": row["label"], "text": row["text"]} for _, row in df.iterrows()]
            )
        except ServiceWarning as warning:
            st.warning(str(warning))
    else:
        st.info("OpenAI key missing. Using VADER fallback for sentiment; summary disabled.", icon="ℹ️")

    render_summary(summary_payload)
    render_source_explorer(df)

    csv_data = df.to_csv(index=False).encode("utf-8")
    excel_data = _build_excel(df)
    pdf_data = _build_pdf(summary_payload, df)
    col_csv, col_excel, col_pdf = st.columns(3)
    with col_csv:
        st.download_button(
            "⬇️ Export CSV",
            data=csv_data,
            file_name="reputation_radar.csv",
            mime="text/csv",
        )
    with col_excel:
        st.download_button(
            "⬇️ Export Excel",
            data=excel_data,
            file_name="reputation_radar.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with col_pdf:
        st.download_button(
            "⬇️ Export PDF Summary",
            data=pdf_data,
            file_name="reputation_radar_summary.pdf",
            mime="application/pdf",
        )

    st.success("Analysis complete! Review the insights above.")


if __name__ == "__main__":
    main()
