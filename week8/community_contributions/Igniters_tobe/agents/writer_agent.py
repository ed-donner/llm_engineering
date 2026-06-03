from langchain_core.prompts import ChatPromptTemplate
from Igniters_tobe.config import get_llm

def get_writer_agent(model_name=None):
    """Returns the writer agent logic (using a simple chain)."""
    llm = get_llm(model_name) if model_name else get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional Writer Agent. Your task is to synthesize verified facts into a short, clear explanation. Do not mention any technical challenges, scraping errors, or tool failures. If the input is empty, contains error messages, or if you cannot verify the request with the facts provided, simply respond with: 'couldn't verify these information'."),
        ("human", "Verified Facts: {facts}\n\nGenerate the final response:"),
    ])

    chain = prompt | llm
    return chain

def run_writing(facts: str, model_name=None) -> str:
    """Executes the writer agent and returns the final text."""
    chain = get_writer_agent(model_name)
    result = chain.invoke({"facts": facts})
    return result.content
