SYSTEM_PROMPT = """You are an expert Python developer specializing in writing unit tests.
Your task is to write comprehensive pytest test cases for given Python code.

Rules:
- Write tests using pytest (not unittest)
- Cover: happy path, edge cases, and error cases
- Use descriptive test function names (test_<function>_<scenario>)
- Do NOT include import statements for the source module (it will be handled automatically)
- Return ONLY the test code inside ```python blocks
"""

def build_prompt(documented_code: str) -> str:
    return f"""Write comprehensive pytest unit tests for all functions in this code.
Cover happy path, edge cases, and expected exceptions.
Do NOT add import for the source module.

`````python
{documented_code}
````"""