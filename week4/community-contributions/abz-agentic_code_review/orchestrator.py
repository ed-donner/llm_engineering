from openai import OpenAI
import os
from agents import docstring_agent, testgen_agent, selfheal_agent
from utils.code_runner import run_pytest

MAX_HEAL_ATTEMPTS = 3

def build_clients():
    gemini_client = OpenAI(
        api_key=os.getenv("GOOGLE_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    openrouter_client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )
    ollama_client = OpenAI(
        api_key="ollama",
        base_url="http://localhost:11434/v1"
    )
    return gemini_client, openrouter_client, ollama_client

def run_pipeline(python_code: str):
    """
    Run full agentic pipeline:
    Step 1 → Docstring → Step 2 → Unit Test → Step 3 → Self-Heal loop
    
    Yields a log string for display in the UI via streaming.
    """
    gemini, openrouter, ollama = build_clients()

    # STEP 1: DOCSTRING 
    yield "**Step 1/3:** Generating docstrings..."
    
    documented_code = docstring_agent.run(
        python_code=python_code,
        model="gemini-3.1-flash-lite",
        client=gemini
    )
    yield "**Step 1 done.** Docstrings added.\n"

    # STEP 2: UNIT TEST 
    yield "**Step 2/3:** Writing unit tests..."
    
    test_code = testgen_agent.run(
        documented_code=documented_code,
        model="recursive/flint-v1.0:free",
        client=openrouter
    )
    yield "**Step 2 done.** Unit tests generated.\n"

    # STEP 3: SELF-HEAL LOOP 
    yield "**Step 3/3:** Running tests + self-healing loop...\n"
    
    final_code = documented_code
    test_result = None

    for attempt in range(1, MAX_HEAL_ATTEMPTS + 1):
        test_result = run_pytest(final_code, test_code)
        
        if test_result.passed:
            yield f"**All tests passed** on attempt {attempt}!\n"
            break
        
        yield f"**Attempt {attempt}/{MAX_HEAL_ATTEMPTS}:** Tests failed.\n"
        yield f"```\n{test_result.output[-1500:]}\n```\n"  # trim output panjang
        
        if attempt < MAX_HEAL_ATTEMPTS:
            final_code = selfheal_agent.run(
                source_code=final_code,
                test_code=test_code,
                errors=test_result.output,
                attempt=attempt,
                model="qwen2.5-coder:7b",
                client=ollama
            )
    else:
        yield "**Self-healing exhausted.** Max attempts reached. Review manually.\n"

    yield {
        "documented_code": final_code,
        "test_code": test_code,
        "test_result": test_result
    }