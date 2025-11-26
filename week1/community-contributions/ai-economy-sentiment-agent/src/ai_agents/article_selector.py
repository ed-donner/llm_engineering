"""
AI Agent 1: Intelligent article selection based on relevance
"""

import json
import re
from typing import List, Dict, Any
from openai import OpenAI

from config import OLLAMA_BASE_URL, AI_MODEL, MAX_SELECTED_ARTICLES


client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")


def select_relevant_articles(
    articles: List[Dict[str, Any]], 
    max_articles: int = MAX_SELECTED_ARTICLES
) -> List[Dict[str, Any]]:
    """
    Use AI to select the most relevant articles for financial/economic analysis.
    
    Args:
        articles: List of article dictionaries from RSS feed
        max_articles: Maximum number of articles to select (default: 12)
    
    Returns:
        List of selected article dictionaries
    """
    if not articles:
        return []
    
    # Prepare article list for AI
    articles_list = ""
    for i, article in enumerate(articles):
        articles_list += f"[{i}] {article['title']}\n"
    
    print(f"Sending {len(articles)} articles to AI for relevance filtering...\n")
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": f"""You are a JSON API that returns ONLY a JSON array - absolutely nothing else.

Task: Select {max_articles} article indices most relevant for financial/economic market analysis.

Rules:
- Include: Fed, inflation, jobs, GDP, interest rates, markets, economic policy
- Exclude: Celebrity, sports, entertainment, non-economic news

CRITICAL: Respond with ONLY a JSON array of numbers. Example: [0, 3, 7, 12, 15, 19, 22, 25, 28, 31, 34, 37]

NO explanations. NO questions. NO text. ONLY the JSON array."""},
                {"role": "user", "content": f"Article list:\n\n{articles_list}\n\nReturn ONLY JSON array of {max_articles} best indices:"},
            ],
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"Raw AI response: '{ai_response}'\n")
        
        # Extract JSON even if wrapped in text
        json_match = re.search(r'\[[\d\s,]+\]', ai_response)
        if json_match:
            ai_response = json_match.group(0)
        
        selected_indices = json.loads(ai_response)
        
        # Validate
        if not isinstance(selected_indices, list):
            raise ValueError("Not a list")
        
        # Filter valid indices
        selected_indices = [i for i in selected_indices if isinstance(i, int) and 0 <= i < len(articles)][:max_articles]
        
        if not selected_indices:
            print("[WARN] No valid indices, using first articles")
            return articles[:max_articles]
        
        selected = [articles[i] for i in selected_indices]
        
        print(f"[OK] AI selected {len(selected)} articles:")
        for art in selected:
            print(f"  - {art['title'][:75]}...")
        
        return selected
        
    except Exception as e:
        print(f"[WARN] AI selection failed ({str(e)[:80]})")
        print(f"  Falling back to first {max_articles} articles\n")
        return articles[:max_articles]

