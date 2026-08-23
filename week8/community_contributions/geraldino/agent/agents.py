"""

This file contains all agents in one file:
  - Data models   : ScrapedDeal, Deal, DealSelection, Opportunity
  - ScannerAgent  : fetches RSS feeds + GPT-5-mini deal selection
  - PricerAgent   : calls fine-tuned Qwen2.5-3B on Modal for price estimation
  - MessagingAgent: sends deal notifications via Gmail SMTP

"""

import logging
import os
import re
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Self

import feedparser
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from pydantic import BaseModel, Field
from tqdm import tqdm

logger = logging.getLogger(__name__)

# DATA MODELS  (deals.py)

FEEDS = [
    "https://www.dealnews.com/c142/Electronics/?rss=1",
    "https://www.dealnews.com/c39/Computers/?rss=1",
    "https://www.dealnews.com/f1912/Smart-Home/?rss=1",

    # "https://www.dealnews.com/f1913/Automotive/?rss=1",
    # "https://www.dealsnews.com/c196/Home-Garden/?rss=1",
]


def extract(html_snippet: str) -> str:
    soup = BeautifulSoup(html_snippet, "html.parser")
    snippet_div = soup.find("div", class_="snippet summary")
    if snippet_div:
        description = snippet_div.get_text(strip=True)
        description = BeautifulSoup(description, "html.parser").get_text()
        description = re.sub("<[^<]+?>", "", description)
        result = description.strip()
    else:
        result = html_snippet
    return result.replace("\n", " ")


class ScrapedDeal:
    """A class to represent a deal retrieved from an RSS feed."""

    title:    str
    summary:  str
    url:      str
    details:  str
    features: str

    def __init__(self, entry: Dict):
        self.title   = entry["title"]
        self.summary = extract(entry["summary"])
        self.url     = entry["links"][0]["href"]
        try:
            response = requests.get(self.url, timeout=10)
            soup     = BeautifulSoup(response.content, "html.parser")
            section  = soup.find("div", class_="content-section")
            if section:
                content = section.get_text().replace("\nmore", "").replace("\n", " ")
                if "Features" in content:
                    self.details, self.features = content.split("Features", 1)
                else:
                    self.details, self.features = content, ""
            else:
                self.details, self.features = self.summary, ""
        except Exception as exc:
            logger.warning(f"Could not fetch deal page '{self.title[:40]}': {exc}")
            self.details, self.features = self.summary, ""
        self.truncate()

    def truncate(self):
        self.title    = self.title[:100]
        self.details  = self.details[:500]
        self.features = self.features[:500]

    def __repr__(self):
        return f"<{self.title}>"

    def describe(self) -> str:
        return (
            f"Title: {self.title}\n"
            f"Details: {self.details.strip()}\n"
            f"Features: {self.features.strip()}\n"
            f"URL: {self.url}"
        )

    @classmethod
    def fetch(cls, show_progress: bool = False) -> List[Self]:
        deals, feed_iter = [], tqdm(FEEDS) if show_progress else FEEDS
        for feed_url in feed_iter:
            logger.info(f"Fetching feed: {feed_url}")
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:
                    try:
                        deals.append(cls(entry))
                    except Exception as exc:
                        logger.warning(f"Skipping entry: {exc}")
                    time.sleep(0.05)
            except Exception as exc:
                logger.warning(f"Could not parse feed {feed_url}: {exc}")
        logger.info(f"Total scraped deals: {len(deals)}")
        return deals


class Deal(BaseModel):
    product_description: str = Field(
        description=(
            "Your clearly expressed summary of the product in 3-4 sentences. "
            "Details of the item are much more important than why it's a good deal. "
            "Avoid mentioning discounts and coupons; focus on the item itself."
        )
    )
    price: float = Field(
        description=(
            "The actual price of this product as advertised. "
            "If a deal says '$100 off the usual $300 price', respond with 200."
        )
    )
    url: str = Field(description="The URL of the deal as provided in the input.")


class DealSelection(BaseModel):
    deals: List[Deal] = Field(
        description=(
            "The 5 deals with the most detailed, high quality description "
            "and the most clear price."
        )
    )


class Opportunity(BaseModel):
    """A deal where our model estimates the item is worth more than listed."""
    deal:     Deal
    estimate: float   # model's estimated real market value
    discount: float   # saving: estimate - price




# SCANNER AGENT
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """\
You identify and summarize the 5 most detailed deals from a list, selecting those with
the most detailed, high quality description and the most clear price.
Respond strictly in JSON. Provide the price as a number derived from the description.
If the price of a deal isn't clear, do not include it.
Be careful with products described as "$XXX off" or "reduced by $XXX" — that is NOT
the actual price. Only include products when you are highly confident about the price.\
"""

USER_PROMPT_PREFIX = """\
Respond with the most promising 5 deals from this list, selecting those with the most
detailed product description and a clear price greater than 0.
Rephrase the description as a summary of the product itself, not the terms of the deal.
Write a short paragraph in product_description for each of the 5 items you select.
Be careful with "$XXX off" or "reduced by $XXX" — that is NOT the actual price.

Deals:

"""
USER_PROMPT_SUFFIX = "\n\nInclude exactly 5 deals, no more."


class ScannerAgent:
    """
    Fetches RSS deals, sends to GPT-4o-mini for structured selection.
    Returns a DealSelection of the 5 best deals with confirmed prices.
    """
    MODEL = "gpt-4o-mini"

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("ScannerAgent ready.")

    def _make_user_prompt(self, scraped: list) -> str:
        return USER_PROMPT_PREFIX + "\n\n".join(d.describe() for d in scraped) + USER_PROMPT_SUFFIX

    def scan(self, show_progress: bool = False) -> DealSelection:
        logger.info("ScannerAgent: fetching deals from RSS feeds…")
        scraped = ScrapedDeal.fetch(show_progress=show_progress)
        if not scraped:
            return DealSelection(deals=[])
        logger.info(f"ScannerAgent: sending {len(scraped)} deals to {self.MODEL}…")
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": self._make_user_prompt(scraped)},
        ]
        response = self.client.beta.chat.completions.parse(
            model=self.MODEL, messages=messages, response_format=DealSelection
        )
        result = response.choices[0].message.parsed
        logger.info(f"ScannerAgent: selected {len(result.deals)} deals.")
        for i, d in enumerate(result.deals, 1):
            logger.info(f"  {i}. ${d.price:.2f} — {d.product_description[:60]}…")
        return result



# PRICER AGENT 
# ══════════════════════════════════════════════════════════════════════════════

MIN_DISCOUNT = 20.0   # minimum $ savings to allow a deal to be considered


class PricerAgent:
    """
    Calls the Modal-deployed Qwen2.5-3B service remotely.
    Model loads once in the cloud and stays warm between calls.
    Deploy first with: modal deploy pricer_modal.py
    """

    def __init__(self):
        self.pricer = self._connect()

    def _connect(self):
        """Connect to the deployed Modal service."""
        try:
            import modal
            cls    = modal.Cls.from_name("smart-deal-pricer", "Pricer")
            pricer = cls()
            logger.info("PricerAgent: connected to Modal service.")
            return pricer
        except Exception as exc:
            logger.error(f"PricerAgent: could not connect to Modal — {exc}")
            logger.error("Make sure you have run: modal deploy pricer_modal.py")
            return None

    def _price(self, deal: Deal) -> Optional[float]:
        """Call the Modal service to estimate price for one deal."""
        if not self.pricer:
            return None
        try:
            estimate = self.pricer.price.remote(deal.product_description)
            logger.info(
                f"  '{deal.product_description[:45]}…' "
                f"listed=${deal.price} → est=${estimate:.2f}"
            )
            return float(estimate) if estimate else None
        except Exception as exc:
            logger.warning(f"Modal call failed: {exc}")
            return None

    def price(self, selection: DealSelection) -> list[Opportunity]:
        logger.info(f"PricerAgent: pricing {len(selection.deals)} deals via Modal…")
        opportunities = []
        for deal in selection.deals:
            estimate = self._price(deal)
            if estimate and estimate > 0 and deal.price > 0:
                discount = estimate - deal.price
                if discount >= MIN_DISCOUNT:
                    opportunities.append(
                        Opportunity(deal=deal, estimate=estimate, discount=discount)
                    )
        opportunities.sort(key=lambda o: o.discount, reverse=True)
        logger.info(
            f"PricerAgent: {len(opportunities)} opportunities (discount ≥ ${MIN_DISCOUNT})"
        )
        return opportunities


# MESSAGING AGENT 
# ══════════════════════════════════════════════════════════════════════════════

def _deal_block(opp: Opportunity) -> str:
    saving     = opp.estimate - opp.deal.price
    saving_pct = round((saving / opp.estimate) * 100) if opp.estimate > 0 else 0
    return (
        f"<hr>"
        f"<p>{opp.deal.product_description}</p>"
        f"<p>"
        f"<b>Listed:</b> ${opp.deal.price:,.2f}<br>"
        f"<b>Estimated worth:</b> ${opp.estimate:,.2f}<br>"
        f"<b>You save:</b> ${saving:,.2f} ({saving_pct}% off)<br>"
        f"<a href='{opp.deal.url}'>View deal</a>"
        f"</p>"
    )


def _send(subject: str, html: str, plain: str) -> bool:
    smtp_host     = os.getenv("SMTP_HOST",     "smtp.gmail.com")
    smtp_port     = int(os.getenv("SMTP_PORT", "587"))
    smtp_user     = os.getenv("SMTP_USER",     "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    email_from    = os.getenv("EMAIL_FROM",    smtp_user)
    email_to      = os.getenv("EMAIL_TO",      "")

    if not all([smtp_user, smtp_password, email_to]):
        logger.error("SMTP credentials or EMAIL_TO not set — check your .env")
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"], msg["From"], msg["To"] = subject, email_from, email_to
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.ehlo(); s.starttls(); s.login(smtp_user, smtp_password)
            s.sendmail(email_from, email_to, msg.as_string())
        logger.info(f"Email sent to {email_to}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP auth failed — use a Gmail App Password: https://support.google.com/accounts/answer/185833")
        return False
    except Exception as exc:
        logger.error(f"Email failed: {exc}")
        return False


class MessagingAgent:

    def alert(self, opportunity: Opportunity) -> bool:
        """Called when user clicks a row in the Gradio UI."""
        return self.notify(
            opportunity.deal.product_description,
            opportunity.deal.price,
            opportunity.estimate,
            opportunity.deal.url,
        )

    def push(self, message: str) -> bool:
        logger.info(f"Push: {message}")
        return _send("Smart Deal Digest", f"<p>{message}</p>", message)

    def notify(self, description: str, price: float, estimate: float, url: str) -> bool:
        saving     = estimate - price
        saving_pct = round((saving / estimate) * 100) if estimate > 0 else 0
        subject    = f"Deal alert: save ${saving:,.0f} ({saving_pct}% off)"
        plain = (
            f"{description}\n\n"
            f"  Listed:          ${price:,.2f}\n"
            f"  Estimated worth: ${estimate:,.2f}\n"
            f"  You save:        ${saving:,.2f} ({saving_pct}% off)\n\n"
            f"  {url}"
        )
        html = (
            f"<p>{description}</p>"
            f"<p>"
            f"<b>Listed:</b> ${price:,.2f}<br>"
            f"<b>Estimated worth:</b> ${estimate:,.2f}<br>"
            f"<b>You save:</b> ${saving:,.2f} ({saving_pct}% off)<br>"
            f"<a href='{url}'>View deal</a>"
            f"</p>"
        )
        logger.info(f"Notify: {description[:50]}… save=${saving:.2f} ({saving_pct}%)")
        return _send(subject, html, plain)

    def send_digest(self, opportunities: list) -> bool:
        if not opportunities:
            logger.info("No opportunities — skipping email.")
            return True
        today   = datetime.now().strftime("%d %b %Y")
        count   = len(opportunities)
        subject = f"Smart Deal Digest — {count} deal{'s' if count != 1 else ''} found ({today})"
        blocks  = "".join(_deal_block(o) for o in opportunities)
        html    = (
            f"<h3>Smart Deal Digest — {today}</h3>"
            f"<p>{count} deal{'s' if count != 1 else ''} where the listed price is below estimated market value.</p>"
            f"{blocks}"
            f"<hr><p><small>Prices are AI estimates — verify before buying.</small></p>"
        )
        plain = "\n\n".join(
            f"{o.deal.product_description[:80]}\n"
            f"  Listed: ${o.deal.price:,.2f} | Worth: ${o.estimate:,.2f} | You save: ${o.discount:,.2f}\n"
            f"  {o.deal.url}"
            for o in opportunities
        )
        return _send(subject, html, plain)
