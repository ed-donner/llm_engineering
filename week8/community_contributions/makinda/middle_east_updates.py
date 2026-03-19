"""
Middle East conflict news aggregator.

Fetches RSS from CNN, Al Jazeera, and BBC; uses GPT-4.1-nano to summarize
updates about the conflict in the Middle East; sends the digest via Telegram.

"""

import os
import json
import xml.etree.ElementTree as ET
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
import requests


_root = Path(__file__).resolve().parents[3]  
for path in [_root, Path.cwd(), Path(__file__).resolve().parent]:
    env_file = path / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
        break

MODEL = "gpt-4.1-nano-2025-04-14"

RSS_FEEDS = [
    ("CNN World", "http://rss.cnn.com/rss/cnn_world.rss"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("BBC Middle East", "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml"),
]

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_TELEGRAM_MESSAGE = 4096


def _parse_rss(xml_bytes: bytes, source: str) -> list[dict]:
    """Parse RSS XML into list of entries with title, url, description, pubDate, source."""
    entries = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return entries
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc_el = item.find("description")
        desc = ""
        if desc_el is not None and desc_el.text:
            desc = desc_el.text.strip()
        elif desc_el is not None and len(desc_el) > 0:
            desc = "".join(desc_el.itertext()).strip()
        pub = (item.findtext("pubDate") or "").strip()
        if title and link:
            entries.append({
                "title": title,
                "url": link,
                "description": (desc or "")[:500],
                "pubDate": pub,
                "source": source,
            })
    return entries


def fetch_all_rss() -> list[dict]:
    """Fetch RSS from CNN, Al Jazeera, BBC and return combined entries (deduplicated by url)."""
    all_entries: list[dict] = []
    seen: set[str] = set()

    for source_name, feed_url in RSS_FEEDS:
        try:
            req = urllib.request.Request(
                feed_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; MiddleEastUpdates/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml_bytes = resp.read()
            for entry in _parse_rss(xml_bytes, source_name):
                if entry["url"] not in seen:
                    seen.add(entry["url"])
                    all_entries.append(entry)
        except Exception as e:
            print(f"Could not fetch {source_name} ({feed_url}): {e}")

    return all_entries


def summarize_middle_east_updates(entries: list[dict], client: OpenAI) -> str:
    """
    Use GPT-4.1-nano to filter and summarize entries relevant to the conflict in the Middle East.
    Returns a concise digest suitable for Telegram.
    """
    if not entries:
        return "No RSS entries fetched."

    # Limit input size to avoid token limits
    sample = []
    for e in entries[:60]:
        sample.append({
            "title": e["title"],
            "description": (e.get("description") or "")[:400],
            "source": e["source"],
            "url": e["url"],
        })
        if len(json.dumps(sample, ensure_ascii=False)) > 11_000:
            sample.pop()
            break
    payload = json.dumps(sample, ensure_ascii=False)

    system_prompt = """You are a news digest writer. Given a list of RSS news entries from CNN, Al Jazeera, and BBC, you must:
1. Select only entries that are clearly about the conflict in the Middle East (e.g. Israel, Gaza, Palestine, Iran, Lebanon, Syria, Yemen, regional tensions, war, ceasefire, hostages, humanitarian crisis in the region).
2. Write a single, concise digest (in plain text, no markdown) of the latest updates. Group by theme if helpful. Include source names and one line per story with the key fact; no bullet points needed if you use short paragraphs.
3. Keep the total digest under 3500 characters so it can be sent in one Telegram message.
4. If none of the entries are about the Middle East conflict, say: "No relevant Middle East conflict updates in the current headlines."
Do not invent stories; only summarize from the given entries."""

    user_prompt = f"RSS entries (title, description, source, url):\n{payload}"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
    )
    text = (response.choices[0].message.content or "").strip()
    if len(text) > MAX_TELEGRAM_MESSAGE:
        text = text[: MAX_TELEGRAM_MESSAGE - 50] + "\n\n[...truncated]"
    return text


def send_telegram(text: str) -> bool:
    """Send text to Telegram using TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
        return False
    url = TELEGRAM_API.format(token=token)
    try:
        r = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"Telegram send failed: {e}")
        return False


def run():
    """Fetch RSS, summarize with GPT-4.1-nano, send via Telegram."""
    entries = fetch_all_rss()
    print(f"Fetched {len(entries)} unique RSS entries")

    client = OpenAI()
    digest = summarize_middle_east_updates(entries, client)
    print("Digest preview:", digest[:200] + "..." if len(digest) > 200 else digest)

    if send_telegram(digest):
        print("Update sent to Telegram.")
    else:
        print("Telegram send failed; digest printed above.")


def run_pipeline_with_status(send_to_telegram: bool):
    """
    Generator that runs the full pipeline and yields (status, digest, headlines_table)
    for real-time Gradio updates.
    """
    status = "Fetching RSS from CNN, Al Jazeera, BBC..."
    yield status, "", []

    entries = fetch_all_rss()
    status = f"Fetched {len(entries)} entries. Summarizing with {MODEL}..."
    # Build table: source, title, url (for display)
    table = [[e["source"], e["title"][:80] + ("..." if len(e["title"]) > 80 else ""), e["url"]] for e in entries[:30]]
    yield status, "", table

    client = OpenAI()
    digest = summarize_middle_east_updates(entries, client)

    if send_to_telegram:
        status = "Sending digest to Telegram..."
        yield status, digest, table
        ok = send_telegram(digest)
        status = "Done. Sent to Telegram." if ok else "Done. Telegram send failed (check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)."
    else:
        status = "Done. (Telegram skipped.)"

    yield status, digest, table


def build_ui():
    """Build and return the Gradio Blocks app for real-time display."""
    import gradio as gr

    with gr.Blocks(title="Middle East Conflict Updates", theme=gr.themes.Soft()) as ui:
        gr.Markdown(
            "# Middle East Conflict Updates\n"
            "RSS from **CNN**, **Al Jazeera**, and **BBC** → summarized by **GPT-4.1-nano** → optional Telegram."
        )
        send_telegram_cb = gr.Checkbox(label="Also send digest to Telegram", value=True)
        run_btn = gr.Button("Fetch & summarize", variant="primary")
        status_box = gr.Textbox(
            label="Status",
            value="Click 'Fetch & summarize' to load latest headlines and generate the digest.",
            interactive=False,
            lines=2,
        )
        digest_box = gr.Textbox(
            label="Digest (Middle East conflict updates)",
            value="",
            interactive=False,
            lines=18,
            max_lines=30,
        )
        table = gr.Dataframe(
            headers=["Source", "Title", "URL"],
            label="Latest headlines (first 30)",
            interactive=False,
            wrap=True,
        )

        def run_and_update(send_to_telegram):
            for st, dig, tbl in run_pipeline_with_status(send_to_telegram):
                yield st, dig, tbl

        run_btn.click(
            fn=run_and_update,
            inputs=[send_telegram_cb],
            outputs=[status_box, digest_box, table],
        )

    return ui


def launch_ui(share: bool = False, inbrowser: bool = True):
    """Launch the Gradio UI."""
    ui = build_ui()
    ui.launch(share=share, inbrowser=inbrowser)


if __name__ == "__main__":
    import sys
    if "--cli" in sys.argv:
        run()
    else:
        launch_ui()
