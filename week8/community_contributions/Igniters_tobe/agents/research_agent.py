from langgraph.prebuilt import create_react_agent
from Igniters_tobe.config import get_llm
from Igniters_tobe.tools.web_search import web_search

SYSTEM_PROMPT = (
    "You are a world-class Research Agent. Your goal is to gather detailed "
    "information about a topic using the web_search tool. Be thorough and "
    "provide comprehensive raw data for the Fact Checker."
)

def get_research_agent(model_name=None):
    """Returns a research agent graph using langgraph."""
    llm = get_llm(model_name) if model_name else get_llm()
    return create_react_agent(llm, tools=[web_search], prompt=SYSTEM_PROMPT)

def run_research(query: str, model_name=None) -> str:
    """Executes the research agent and returns the result."""
    agent = get_research_agent(model_name)
    result = agent.invoke({"messages": [("user", query)]})
    return result["messages"][-1].content
