"""
Earnings sentiment analysis using yfinance and AI
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Any
from openai import OpenAI
import json
import re
import time

from config import OLLAMA_BASE_URL, AI_MODEL


def get_earnings_sentiment() -> Dict[str, Any]:
    """
    Fetch recent earnings data for major companies and analyze sentiment.
    
    Analyzes earnings reports, guidance, and analyst reactions for major
    market-moving companies to gauge corporate sentiment.
    
    Returns:
        Dict containing earnings calendar and AI-analyzed sentiment
    """
    try:
        print("Fetching earnings data...")
        
        # Major market-moving tickers
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META']
        
        earnings_data = []
        today = datetime.now()
        rate_limited = False
        
        for ticker_symbol in tickers:
            # Add small delay to avoid rate limiting
            time.sleep(0.5)
            try:
                ticker = yf.Ticker(ticker_symbol)
                info = ticker.info
                
                # Check if we got valid info
                if not info or 'symbol' not in info:
                    print(f"  [SKIP] {ticker_symbol}: No data available")
                    continue
                
                # Get earnings date if available
                earnings_date = info.get('earningsDate')
                if isinstance(earnings_date, list) and len(earnings_date) > 0:
                    earnings_date = earnings_date[0]
                
                # Collect financial data (don't require earnings_date)
                company_name = info.get('longName', ticker_symbol)
                
                # Build data dict - include even if some fields are missing
                data = {
                    'ticker': ticker_symbol,
                    'company': company_name,
                    'earnings_date': str(earnings_date) if earnings_date else 'Not Available',
                    'revenue_growth': info.get('revenueGrowth'),
                    'earnings_growth': info.get('earningsGrowth'),
                    'profit_margins': info.get('profitMargins'),
                    'analyst_target': info.get('targetMeanPrice'),
                    'current_price': info.get('currentPrice'),
                    'recommendation': info.get('recommendationKey')
                }
                
                # Only add if we have at least some financial metrics
                has_data = any([
                    data['revenue_growth'] is not None,
                    data['earnings_growth'] is not None,
                    data['profit_margins'] is not None,
                    data['current_price'] is not None
                ])
                
                if has_data:
                    earnings_data.append(data)
                    print(f"  [OK] {ticker_symbol}: {company_name}")
                else:
                    print(f"  [SKIP] {ticker_symbol}: No financial metrics available")
                    
            except Exception as e:
                error_msg = str(e)
                if 'rate limit' in error_msg.lower() or 'too many requests' in error_msg.lower():
                    rate_limited = True
                print(f"  [WARN] {ticker_symbol}: {error_msg[:60]}")
                continue
        
        if not earnings_data:
            if rate_limited:
                return {
                    'error': 'Rate limited by yfinance API',
                    'note': 'Earnings data temporarily unavailable due to rate limiting. Wait a few minutes and try again.',
                    'suggestion': 'The analysis can continue without earnings data.'
                }
            return {
                'error': 'No earnings data available',
                'note': 'Could not fetch earnings information from any ticker'
            }
        
        # Use AI to analyze overall earnings sentiment
        client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
        
        earnings_summary = json.dumps(earnings_data, indent=2)
        
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert financial analyst analyzing corporate earnings sentiment.

Based on the earnings data provided (revenue growth, earnings growth, profit margins, analyst recommendations), provide:

1. Overall Market Sentiment: Bullish/Neutral/Bearish
2. Key Observations: 2-3 bullet points about trends
3. Confidence Level: High/Medium/Low

Keep your response concise and focused on actionable insights."""
                },
                {
                    "role": "user",
                    "content": f"Analyze the earnings sentiment from these major tech companies:\n\n{earnings_summary}"
                }
            ],
            temperature=0.3
        )
        
        sentiment_analysis = response.choices[0].message.content
        
        result = {
            'companies_analyzed': len(earnings_data),
            'earnings_data': earnings_data,
            'ai_sentiment_analysis': sentiment_analysis
        }
        
        print(f"[OK] Earnings sentiment analyzed for {len(earnings_data)} companies")
        return result
        
    except Exception as e:
        print(f"[WARN] Earnings Sentiment: Error - {str(e)[:80]}")
        return {
            'error': str(e)[:80],
            'note': 'Earnings sentiment data unavailable'
        }





