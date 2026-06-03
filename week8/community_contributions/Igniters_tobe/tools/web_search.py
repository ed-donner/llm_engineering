import os
from langchain_core.tools import tool

@tool
def web_search(query: str) -> str:
    """Search the web for current information, news, and facts. Input should be a search query."""
    # Try SerpAPI first, fall back to DuckDuckGo
    serpapi_key = os.getenv("SERPAPI_API_KEY") or os.getenv("SERP_API_KEY")

    if serpapi_key:
        try:
            from langchain_community.utilities import SerpAPIWrapper
            search = SerpAPIWrapper(serpapi_api_key=serpapi_key)
            return search.run(query)
        except Exception:
            pass  # Fall through to DuckDuckGo

    # Fallback: DuckDuckGo via ddgs
    from ddgs import DDGS
    results = DDGS().text(query, max_results=5)
    if not results:
        return "No search results found."
    return "\n\n".join(
        f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}"
        for r in results
    )
