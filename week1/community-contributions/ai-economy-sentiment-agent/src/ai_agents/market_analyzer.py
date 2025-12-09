"""
AI Agent 3: Comprehensive market analysis integrating all data sources
"""

from typing import Dict, Any
from openai import OpenAI

from config import OLLAMA_BASE_URL, AI_MODEL


client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")


def generate_comprehensive_analysis(
    market_data: Dict[str, Any],
    sector_data: Dict[str, Any],
    fear_greed: tuple,
    polymarket: Dict[str, Any],
    earnings: Dict[str, Any],
    economic_data: Dict[str, float],
    news_sentiment: str,
    market_is_open: bool
) -> str:
    """
    Generate comprehensive market analysis using AI to synthesize all data.
    
    Args:
        market_data: Dictionary of market performance data
        sector_data: Dictionary of sector ETF performance data
        fear_greed: Tuple of (score, rating) for Fear & Greed Index
        polymarket: Dictionary of Polymarket prediction market data
        earnings: Dictionary of earnings sentiment data
        economic_data: Dictionary of economic indicators
        news_sentiment: String output from news sentiment analysis
        market_is_open: Boolean indicating if market is currently open
    
    Returns:
        String containing comprehensive AI analysis
    """
    # Build market summary
    market_summary = "COMPREHENSIVE MARKET DATA:\n\n"
    
    # Market Performance
    market_summary += "MARKET PERFORMANCE:\n"
    for name, data in market_data.items():
        if data:
            status = "LIVE" if data.get('is_live') else "Last Close"
            market_summary += f"- {name}: ${data['current_price']:.2f} ({data['daily_change_pct']:+.2f}%) [{status}]\n"
        else:
            market_summary += f"- {name}: Data unavailable\n"
    
    # Sector Performance
    if sector_data:
        market_summary += f"\nSECTOR PERFORMANCE:\n"
        valid_sectors = [(s, d) for s, d in sector_data.items() if d and isinstance(d, dict) and 'daily_change_pct' in d]
        if valid_sectors:
            # Sort by daily performance
            sorted_sectors = sorted(valid_sectors, key=lambda x: x[1]['daily_change_pct'], reverse=True)
            for sector, data in sorted_sectors:
                market_summary += f"- {sector}: {data['daily_change_pct']:+.2f}% (day), {data['week_change_pct']:+.2f}% (week)\n"
            
            # Add leaders/laggards summary
            if 'leaders' in sector_data:
                leaders = sector_data['leaders']
                market_summary += f"\nSector Leaders: {leaders.get('daily_best')} (day), {leaders.get('weekly_best')} (week)\n"
                market_summary += f"Sector Laggards: {leaders.get('daily_worst')} (day), {leaders.get('weekly_worst')} (week)\n"
    
    # Fear & Greed Index
    if fear_greed[0] is not None:
        market_summary += f"\nFEAR & GREED INDEX:\n"
        market_summary += f"- Score: {fear_greed[0]} / 100\n"
        market_summary += f"- Rating: {fear_greed[1].upper()}\n"
    
    # Polymarket Predictions (AI-Selected)
    if polymarket and 'error' not in polymarket and polymarket.get('selected_markets'):
        market_summary += f"\nPOLYMARKET PREDICTIONS (AI-Selected Markets):\n"
        market_summary += f"- AI selected {len(polymarket['selected_markets'])} most relevant prediction markets\n"
        for i, market in enumerate(polymarket['selected_markets'], 1):
            prob = market.get('probability')
            relevance = market.get('relevance', '')
            if prob is not None:
                market_summary += f"  {i}. {market['question']}: {prob * 100:.1f}% probability"
                if relevance:
                    market_summary += f" - {relevance}"
                market_summary += "\n"
    
    # Earnings Sentiment
    if earnings and 'error' not in earnings:
        market_summary += f"\nEARNINGS SENTIMENT:\n"
        market_summary += f"- Companies Analyzed: {earnings.get('companies_analyzed', 0)}\n"
        if earnings.get('ai_sentiment_analysis'):
            market_summary += f"- Analysis: {earnings['ai_sentiment_analysis']}\n"
    
    # Economic Indicators
    market_summary += f"\nECONOMIC INDICATORS:\n"
    if economic_data.get('federal_funds_rate'):
        market_summary += f"- Federal Funds Rate: {economic_data['federal_funds_rate']}%\n"
    if economic_data.get('treasury_10y_yield'):
        market_summary += f"- 10-Year Treasury Yield: {economic_data['treasury_10y_yield']}%\n"
    if economic_data.get('cpi_latest'):
        market_summary += f"- CPI Index: {economic_data['cpi_latest']}\n"
    if economic_data.get('unemployment_rate'):
        market_summary += f"- Unemployment Rate: {economic_data['unemployment_rate']}%\n"
    if economic_data.get('non_farm_payrolls'):
        market_summary += f"- Non-Farm Payrolls: {economic_data['non_farm_payrolls']:,.0f}K\n"
    
    if not any(economic_data.values()):
        market_summary += "- Data temporarily unavailable\n"
    
    # News Sentiment
    market_summary += f"\nNEWS SENTIMENT (Last 7 Days):\n"
    market_summary += f"{news_sentiment}\n"
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": """You are an expert financial analyst that provides comprehensive market sentiment analysis. 

Analyze ALL the data provided and give actionable insights about current market conditions, considering:

1. **Market Sentiment**: 
   - Fear & Greed Index and overall investor psychology
   - Polymarket prediction markets (market consensus on Fed decisions, inflation, economic events)
   - Earnings sentiment from major corporations
2. **Market Performance**: 
   - Stock indices performance (S&P 500, Nasdaq, VIX)
   - Sector rotation and performance (all 11 S&P sectors)
   - Identify which sectors are leading/lagging and what this signals about market conditions
3. **Economic Indicators**: 
   - Interest rates (Federal Funds Rate and Treasury yields) and their trajectory
   - Inflation data (CPI) and implications for Fed policy
   - Employment data (unemployment rate and non-farm payrolls) and labor market health
4. **News Sentiment**: Recent political and economic news that may impact markets

**SECTOR ANALYSIS IS CRITICAL**: 
- Sector rotation reveals market positioning (defensive vs growth)
- Strong Technology/Consumer Discretionary = risk-on
- Strong Utilities/Consumer Staples = risk-off/defensive
- Energy strength often signals inflation concerns
- Financials strength suggests rate optimism
- Explain what the sector performance tells us about investor positioning and market outlook

**IMPORTANT**: Based on the economic indicators provided (inflation, unemployment, interest rates), you must:
- Infer the Federal Reserve's likely positioning on interest rate policy (dovish/hawkish, likelihood of cuts vs holds vs hikes)
- Explain what the economic data suggests about future Fed actions
- Consider the dual mandate: price stability (inflation) and maximum employment

Provide a cohesive analysis that connects ALL these data points and explains how they interact. Consider:
- How sector rotation aligns with or contradicts other signals
- How current economic indicators influence Fed policy expectations
- How Fed policy affects market sentiment and sector performance
- How recent news aligns with or contradicts market sentiment and economic data
- Whether current market conditions align with or diverge from economic fundamentals
- Key risks and opportunities for investors

Structure your response with clear sections and be specific about your Fed policy assessment and sector analysis. Make sure to integrate the news sentiment into your overall analysis.

If any data is unavailable, work with what's provided and note any limitations in your analysis."""},
                {"role": "user", "content": market_summary},
            ],
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating analysis: {str(e)}"

