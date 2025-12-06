"""
AI Agent 2: News sentiment analysis for market impact
"""

from typing import List, Dict, Any
from openai import OpenAI

from config import OLLAMA_BASE_URL, AI_MODEL


client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")


def analyze_news_sentiment(articles: List[Dict[str, Any]]) -> str:
    """
    Use AI to analyze sentiment and market impact from news articles.
    
    Args:
        articles: List of selected article dictionaries
    
    Returns:
        String containing AI sentiment analysis
    """
    if not articles:
        return "No articles available for analysis"
    
    # Prepare news summary for AI
    news_summary = "Recent News Articles (Last 7 Days) - AI Selected as Most Relevant:\n\n"
    
    for i, article in enumerate(articles, 1):
        news_summary += f"Article {i}:\n"
        news_summary += f"Category: {article['category']}\n"
        news_summary += f"Title: {article['title']}\n"
        news_summary += f"Published: {article['pub_date']}\n"
        news_summary += f"Source: {article.get('source', 'Unknown')}\n"
        
        # Include description from RSS
        if article.get('description'):
            news_summary += f"Summary: {article['description']}\n"
        
        # Include full content if available
        if article.get('content'):
            news_summary += f"Full Content: {article['content'][:600]}...\n"
        
        news_summary += "\n"
    
    print("Analyzing news sentiment with AI...\n")
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": """You are a financial news analyst specializing in sentiment analysis for markets.

Analyze the provided news articles about the economy and politics and provide:

1. **Overall Sentiment**: Bullish, Bearish, or Neutral (with confidence level %)
2. **Key Themes**: What are the main topics and concerns across all articles?
3. **Market Impact**: How might these stories collectively affect markets?
4. **Political/Policy Implications**: Any policy changes or political developments that could impact the economy?
5. **Risks & Opportunities**: What should investors watch for based on these stories?

Be specific and cite which article numbers support your analysis. Provide a clear, actionable summary that synthesizes all the news."""},
                {"role": "user", "content": news_summary},
            ],
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error analyzing sentiment: {str(e)}"










