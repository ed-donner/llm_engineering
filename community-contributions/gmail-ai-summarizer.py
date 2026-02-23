# Gmail AI Summarizer
# A simple script to summarize today's Gmail emails using OpenAI's GPT-4o-mini.
# It authenticates with Gmail, fetches today's emails, extracts their content,
# and generates a concise summary for each email based on defined rules.
# author: Javid Hussain Fazaeli

import os
import base64
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv

from openai import OpenAI

load_dotenv()

# ---------- CONFIG ----------
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in .env")

client = OpenAI(api_key=OPENAI_API_KEY)

MODEL = "gpt-4o-mini"  # cheap + good for summaries


SYSTEM_PROMPT = """You summarize emails into a crisp daily digest.
Rules:
- 1-2 sentences max per email.
- Start with who it's from.
- Include any deadlines, required actions, and links (just mention "has link" if long).
- If it's spam/promotional, label it PROMO and summarize in 1 short line.
- If it's urgent/needs reply, label ACTION REQUIRED.
"""


def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def extract_best_body(payload):
    """
    Tries to extract a readable text body from Gmail message payload.
    Prefers text/plain; falls back to text/html if needed.
    """
    def decode(data):
        return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")

    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {}).get("data")

    if body:
        return decode(body)

    parts = payload.get("parts", [])
    if not parts:
        return ""

    # Prefer text/plain
    for p in parts:
        if p.get("mimeType") == "text/plain" and p.get("body", {}).get("data"):
            return decode(p["body"]["data"])

    # Then text/html
    for p in parts:
        if p.get("mimeType") == "text/html" and p.get("body", {}).get("data"):
            return decode(p["body"]["data"])

    # Recurse into nested multipart
    for p in parts:
        if p.get("parts"):
            text = extract_best_body(p)
            if text:
                return text

    return ""


def summarize_email(from_, subject, date_str, body):
    # Keep prompts clean and “Ed Donner style” (system rules, user task)
    user_prompt = f"""Summarize this email for my daily digest.

From: {from_}
Subject: {subject}
Date: {date_str}

Body:
{body[:6000]}  # safety: avoid huge tokens
"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


def main():
    service = get_gmail_service()

    # Gmail query: emails after midnight local time is tricky.
    # Easiest: use Gmail search operator "newer_than:1d" for "today-ish",
    # or use "after:YYYY/MM/DD" based on your local date.
    today = datetime.now().strftime("%Y/%m/%d")
    query = f"after:{today}"

    results = service.users().messages().list(userId="me", q=query, maxResults=20).execute()
    msgs = results.get("messages", [])

    if not msgs:
        print("No emails found for today.")
        return

    print(f"Found {len(msgs)} emails for today (query: {query}).\n")

    for i, m in enumerate(msgs, start=1):
        full = service.users().messages().get(userId="me", id=m["id"], format="full").execute()
        headers = full.get("payload", {}).get("headers", [])

        def h(name):
            for x in headers:
                if x.get("name", "").lower() == name.lower():
                    return x.get("value", "")
            return ""

        from_ = h("From")
        subject = h("Subject")
        date_str = h("Date")

        body = extract_best_body(full.get("payload", {})).strip()

        # Optional: skip if empty body
        if not body:
            body = "(No body found; likely a short/structured email.)"

        summary = summarize_email(from_, subject, date_str, body)
        print(f"{i}. {summary}\n")


if __name__ == "__main__":
    main()
