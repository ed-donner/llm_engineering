from Igniters_tobe.agents.research_agent import run_research
from Igniters_tobe.agents.fact_checker_agent import run_fact_check
from Igniters_tobe.agents.writer_agent import run_writing

def process_research_request(query: str, research_model=None, fact_checker_model=None, writer_model=None):
    """
    Coordinates the multi-agent workflow.
    Yields (partial_answer, logs_so_far) tuples for real-time streaming.
    """
    logs = []

    # 1. Research phase
    logs.append("[Research Agent] Starting research...")
    yield "", "\n\n".join(logs)

    raw_research = run_research(query, model_name=research_model)
    logs.append(f"[Research Agent] Completed. Summary: {raw_research[:300]}...")
    yield "", "\n\n".join(logs)

    # 2. Fact Check phase
    logs.append("[Fact Checker Agent] Verifying information...")
    yield "", "\n\n".join(logs)

    verified_facts = run_fact_check(raw_research, model_name=fact_checker_model)
    logs.append(f"[Fact Checker Agent] Completed. Key facts: {verified_facts[:300]}...")
    yield "", "\n\n".join(logs)

    # 3. Writing phase
    logs.append("[Writer Agent] Generating final response...")
    yield "", "\n\n".join(logs)

    final_response = run_writing(verified_facts, model_name=writer_model)
    logs.append("[Writer Agent] Response ready!")
    yield final_response, "\n\n".join(logs)
