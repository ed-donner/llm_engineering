"""
news_agent_module.py
Contains the agent classes for scraping and summarizing AI news.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import datetime
import requests as req_llm
import os
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

class NewsScannerAgent:
    def __init__(self, sources: Optional[List[str]] = None):
        if sources is None:
            self.sources = [
                "https://feeds.feedburner.com/ai-news",
                "https://www.aitrends.com/feed/",
                "https://www.artificialintelligence-news.com/feed/"
            ]
        else:
            self.sources = sources

    def fetch_articles(self) -> List[Dict]:
        articles = []
        now = datetime.datetime.utcnow()
        seven_days_ago = now - datetime.timedelta(days=7)
        for url in self.sources:
            try:
                resp = requests.get(url, timeout=10)
                soup = BeautifulSoup(resp.text, 'html.parser')
                for item in soup.find_all('item'):
                    title = item.find('title').text if item.find('title') else ''
                    link = item.find('link').text if item.find('link') else ''
                    pub_date = item.find('pubdate').text if item.find('pubdate') else ''
                    desc = item.find('description').text if item.find('description') else ''
                    # Try to parse pub_date and filter for last 7 days
                    include_article = True
                    if pub_date:
                        try:
                            # Try common RSS date formats
                            pub_dt = None
                            for fmt in [
                                '%a, %d %b %Y %H:%M:%S %Z',  # RFC822
                                '%a, %d %b %Y %H:%M:%S %z',  # RFC822 with offset
                                '%Y-%m-%dT%H:%M:%SZ',        # ISO8601
                                '%Y-%m-%d %H:%M:%S',         # Simple
                                '%d %b %Y %H:%M:%S %Z',      # No weekday
                            ]:
                                try:
                                    pub_dt = datetime.datetime.strptime(pub_date, fmt)
                                    break
                                except Exception:
                                    continue
                            if pub_dt:
                                # Convert to UTC if tz-aware
                                if pub_dt.tzinfo:
                                    pub_dt = pub_dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
                                if pub_dt < seven_days_ago:
                                    include_article = False
                        except Exception:
                            pass
                    if include_article:
                        articles.append({
                            'title': title,
                            'link': link,
                            'pub_date': pub_date,
                            'description': desc
                        })
            except Exception as e:
                print(f"Error fetching from {url}: {e}")
        return articles

class SummarizerAgent:
    def __init__(self, use_openai: bool = False, openrouter_api_key: Optional[str] = None):
        self.use_openai = use_openai
        self.openrouter_api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")

    def summarize(self, articles: List[Dict]) -> List[Dict]:
        for article in articles:
            if 'description' in article:
                if self.use_openai and self.openrouter_api_key:
                    try:
                        headers = {
                            "Authorization": f"Bearer {self.openrouter_api_key}",
                            "Content-Type": "application/json"
                        }
                        payload = {
                            "model": "openai/gpt-3.5-turbo",
                            "messages": [
                                {"role": "system", "content": "Summarize the following news article in 2 sentences."},
                                {"role": "user", "content": article['description']}
                            ],
                            "max_tokens": 100
                        }
                        resp = req_llm.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=15)
                        resp.raise_for_status()
                        data = resp.json()
                        summary = data["choices"][0]["message"]["content"].strip()
                        article['summary'] = summary
                    except Exception as e:
                        article['summary'] = article['description'][:200] + '... (extractive)'
                else:
                    article['summary'] = article['description'][:200] + '...'
            else:
                article['summary'] = ''
        return articles

class NewsPlannerAgent:
    def __init__(self, scanner: NewsScannerAgent, summarizer: SummarizerAgent):
        self.scanner = scanner
        self.summarizer = summarizer

    def run(self, sources: Optional[List[str]] = None) -> List[Dict]:
        if sources:
            self.scanner.sources = sources
        articles = self.scanner.fetch_articles()
        summarized = self.summarizer.summarize(articles)
        return summarized

    def send_email_digest(self, articles: List[Dict], to_email: str, subject: str = "Your AI News Digest", send_real_email: bool = False):
        body = "<h2>Latest AI News Digest</h2>"
        for art in articles[:10]:
            body += f"<b>{art['title']}</b><br>"
            body += f"<i>{art['pub_date']}</i><br>"
            body += f"<a href='{art['link']}' target='_blank'>Read more</a><br>"
            body += f"{art['summary']}<br><hr>"
        if not send_real_email:
            print(f"[DEBUG] Would send email to: {to_email}")
            print(f"[DEBUG] Subject: {subject}")
            print("[DEBUG] Email body:")
            print(body)
            return
        # Real email sending
        load_dotenv()
        email_address = os.getenv("EMAIL_ADDRESS")
        email_password = os.getenv("EMAIL_PASSWORD")
        if not email_address or not email_password:
            raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set in your .env file to send real emails.")
        msg = MIMEMultipart()
        msg['From'] = email_address
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(email_address, email_password)
                server.send_message(msg)
            print(f"Email sent to {to_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def generate_wordcloud(self, articles: List[Dict], output_path: str = "wordcloud.png"):
        descriptions = [art.get('description', '') for art in articles if art.get('description', '').strip()]
        if not descriptions:
            print("No article descriptions available to generate a word cloud.")
            return
        text = " ".join(descriptions)
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(output_path)
        plt.close()
