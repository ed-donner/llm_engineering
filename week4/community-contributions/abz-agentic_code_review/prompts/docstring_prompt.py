SYSTEM_PROMPT = """You are an expert Python developer specializing in code documentation.
Your task is to add comprehensive Google-style docstrings to Python code.

Rules:
- Add docstrings to ALL functions, classes, and methods
- Include Args, Returns, Raises sections where relevant
- Keep the original code logic completely unchanged
- Return ONLY the complete documented Python code inside ```python blocks
- Do not add explanations outside the code block
"""

def build_prompt(python_code: str) -> str:
    return f"""Add Google-style docstrings to every function and class in this Python code.
Do not modify the logic. Return the complete documented code.

```````python
{python_code}
``````
"""