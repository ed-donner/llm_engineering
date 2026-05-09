"""
Securities Scanner Agent - fetches securities events (filings, news).
MVP uses mock/synthetic events. Can be extended with SEC EDGAR RSS or Finnhub.
"""

import os
from typing import List, Optional

from agents.agent import Agent
from models.research import SecuritiesEvent

# SEC EDGAR RSS for future use
SEC_EDGAR_RSS = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=&company=&dateb=&owner=include&count=40&output=atom"


class SecuritiesScannerAgent(Agent):
    name = "Securities Scanner"
    color = Agent.CYAN

    def __init__(self):
        self.log("Securities Scanner initializing")
        watched = os.getenv("WATCHED_TICKERS", "AAPL,GOOGL,MSFT,AMZN,NVDA")
        self.watched_tickers = [t.strip() for t in watched.split(",") if t.strip()]
        self.log(f"Watched tickers: {self.watched_tickers}")

    def _mock_events(self) -> List[SecuritiesEvent]:
        """Generate mock securities events for MVP development."""
        mock_data = [
            ("AAPL", "Apple Inc. files 10-K annual report", "https://sec.gov/aapl-10k", "2024-10-28",
             "Apple reported strong iPhone and Services revenue. Dividend increased."),
            ("GOOGL", "Alphabet Q3 earnings beat estimates", "https://sec.gov/googl-q3", "2024-10-25",
             "Google Cloud revenue grew 22% YoY. Search advertising stable."),
            ("MSFT", "Microsoft Azure growth accelerates", "https://sec.gov/msft-10q", "2024-10-24",
             "Microsoft Cloud revenue $35 billion. AI services driving growth."),
            ("AMZN", "Amazon Web Services expansion announced", "https://sec.gov/amzn-10q", "2024-10-31",
             "AWS operating margin improved. New data center regions planned."),
            ("NVDA", "NVIDIA reports record data center revenue", "https://sec.gov/nvda-10q", "2024-11-20",
             "Data center revenue up 409% YoY. AI chip demand remains strong."),
        ]
        return [
            SecuritiesEvent(ticker=t, headline=h, source_url=u, published_at=d, summary=s)
            for t, h, u, d, s in mock_data
            if t in self.watched_tickers
        ]

    def scan(self, memory: List[str] = None) -> Optional[List[SecuritiesEvent]]:
        """
        Scan for securities events. Filters by watched tickers.
        memory: list of URLs already processed (to avoid duplicates).
        Returns list of SecuritiesEvent or None if none found.
        """
        self.log("Scanning for securities events")
        memory = memory or []
        events = self._mock_events()
        # Filter out already-seen URLs
        seen_urls = set(memory)
        events = [e for e in events if e.source_url not in seen_urls]
        if not events:
            self.log("No new securities events found")
            return None
        self.log(f"Found {len(events)} new securities events")
        return events
