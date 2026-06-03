"""
Market Research Synthesizer
Input: Industry keywords → Synthesize market trends, competitors, gaps, growth signals
One API call to LLM + web scraping
"""

import os
import json
import requests
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

load_dotenv(override=True)


class MarketResearchSynthesizer:
    """
    Scrapes articles on a market/industry, sends to LLM for intelligent synthesis.
    Returns: trends, competitors, market gaps, growth signals.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4.1-mini"  # Use cheaper model for efficiency

    def scrape_articles(self, keyword: str, num_results: int = 5) -> list[dict]:
        """
        Scrape articles from multiple sources (news, tech blogs, etc.)
        In production, you'd use a news API or web scraper.
        For demo, we'll use a simple approach with DuckDuckGo or simulate.
        """
        articles = []

        # Simulate scraping from tech news sources
        # In production: use NewsAPI, Bing Search API, or web scraper
        sources = [
            f"https://news.google.com/search?q={keyword}",
            f"https://techcrunch.com/search/{keyword}/",
            f"https://medium.com/search?q={keyword}",
            f"https://news.ycombinator.com/search?q={keyword}",
        ]

        # Try to scrape a couple sources (graceful fallback if blocked)
        for url in sources[:2]:
            try:
                response = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                if response.status_code == 200:
                    # Extract basic text (in production use BeautifulSoup)
                    articles.append(
                        {
                            "url": url,
                            "source": url.split("/")[2],
                            "snippet": f"Article about {keyword} from {url}",
                        }
                    )
            except Exception as e:
                pass  # Skip sources that fail

        # If scraping failed, provide context for LLM to work with
        if not articles:
            articles = [
                {
                    "url": "research_context",
                    "source": "context",
                    "snippet": f"Market research request for keyword: {keyword}",
                }
            ]

        return articles[:num_results]

    def synthesize_market_intelligence(self, keyword: str) -> dict:
        """
        Main function: scrape + synthesize market intelligence in one shot.
        Returns structured JSON with market intel.
        """
        print(f"Researching market: '{keyword}'...")

        # Step 1: Scrape articles
        articles = self.scrape_articles(keyword, num_results=5)
        articles_text = "\n".join(
            [f"- {a['source']}: {a['snippet']}" for a in articles]
        )

        # Step 2: Build intelligent system prompt
        system_prompt = """
You are a senior market analyst and business intelligence expert.
Your task is to synthesize market research and extract actionable business intelligence.
Respond ONLY with valid JSON (no markdown, no explanations).

Return exactly this structure:
{
    "market_summary": "1-2 sentence overview of the market",
    "key_trends": [
        {"trend": "Trend name", "signal_strength": "strong|medium|emerging", "impact": "description"},
        ...
    ],
    "emerging_competitors": [
        {"name": "Company name", "positioning": "Their value prop", "threat_level": "high|medium|low"},
        ...
    ],
    "market_gaps": [
        {"gap": "Unmet need", "opportunity_size": "large|medium|small", "difficulty": "hard|medium|easy"},
        ...
    ],
    "growth_signals": [
        {"signal": "Observable growth indicator", "confidence": "high|medium|low"},
        ...
    ],
    "recommended_angles": [
        "Specific business angle/strategy to pursue"
    ]
}
"""

        user_prompt = f"""
Analyze the market for: {keyword}

Recent articles and signals:
{articles_text}

Based on these signals and your knowledge, synthesize:
1. Key trends in this market
2. Emerging competitors and their positioning
3. Market gaps (unmet needs)
4. Growth signals
5. Recommended business angles

Be specific and actionable. Assume the year is {datetime.now().year}.
"""

        # Step 3: Call LLM
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
        )

        # Step 4: Parse response
        response_text = response.choices[0].message.content.strip()

        # Clean up markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        try:
            market_intel = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback if parsing fails
            market_intel = {
                "error": "Failed to parse LLM response",
                "raw_response": response_text,
            }

        # Step 5: Return structured data
        return {
            "keyword": keyword,
            "timestamp": datetime.now().isoformat(),
            "articles_analyzed": len(articles),
            "intelligence": market_intel,
        }


def main():
    """Demo usage"""
    synthesizer = MarketResearchSynthesizer()

    # Example: analyze AI in healthcare
    keyword = "AI in healthcare 2025"
    result = synthesizer.synthesize_market_intelligence(keyword)

    print("\n" + "=" * 80)
    print(f"MARKET RESEARCH: {keyword}")
    print("=" * 80)
    print(json.dumps(result, indent=2))

    return result


if __name__ == "__main__":
    main()
