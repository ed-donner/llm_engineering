from langgraph.prebuilt import create_react_agent
from Igniters_tobe.config import get_llm
from Igniters_tobe.tools.url_scraper import url_scraper

SYSTEM_PROMPT = (
    "You are a meticulous Fact Checker Agent. Your role is to verify info "
    "from provided research data. Use the url_scraper tool to dig deeper "
    "into specific links if needed. Extract only the most accurate and "
    "relevant facts."
)

def get_fact_checker_agent(model_name=None):
    """Returns a fact checker agent graph using langgraph."""
    llm = get_llm(model_name) if model_name else get_llm()
    return create_react_agent(llm, tools=[url_scraper], prompt=SYSTEM_PROMPT)

def run_fact_check(research_data: str, model_name=None) -> str:
    """Executes the fact checker agent and returns the result."""
    agent = get_fact_checker_agent(model_name)
    message = f"Research Data: {research_data}\n\nTask: Verify the information and extract key facts."
    result = agent.invoke({"messages": [("user", message)]})
    return result["messages"][-1].content
