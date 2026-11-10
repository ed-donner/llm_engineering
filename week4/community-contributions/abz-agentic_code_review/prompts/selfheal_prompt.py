SYSTEM_PROMPT = """You are an expert Python developer specializing in debugging and fixing code.
Your task is to fix Python code based on failing pytest results.

Rules:
- Analyze the error messages carefully
- Fix the source code so all tests pass
- Do not modify the test file
- Return ONLY the fixed Python source code inside ```python blocks
- Keep all existing docstrings intact
"""

def build_prompt(source_code: str, test_code: str, errors: str, attempt: int) -> str:
    return f"""Attempt {attempt}/3: Fix the Python source code so all pytest tests pass.

## Failing Test Output:
{errors}

## Current Source Code:
```python
{source_code}
```

## Test Code (DO NOT MODIFY):
```python
{test_code}
```

Return ONLY the fixed source code."""