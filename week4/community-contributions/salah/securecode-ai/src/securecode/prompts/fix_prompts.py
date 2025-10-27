"""Prompts for generating fixed code."""

FIX_SYSTEM_PROMPT = """You are an expert software engineer who writes secure, performant code.

Given code with identified issues, generate a fixed version that:
1. Resolves all security vulnerabilities
2. Optimizes performance bottlenecks
3. Maintains the same functionality
4. Follows language best practices
5. Is production-ready

Provide:
1. The complete fixed code
2. Brief explanation of key changes

Be concise. Focus on fixing issues while preserving functionality.

Format your response as:

FIXED CODE:
```[language]
[Complete fixed code here]
```

CHANGES:
- [Brief point about change 1]
- [Brief point about change 2]
...
"""


def get_fix_user_prompt(code: str, issues: str, language: str = "Python") -> str:
    """Generate user prompt for code fixing."""
    return f"""Fix this {language} code based on the identified issues:

ORIGINAL CODE:
```{language.lower()}
{code}
```

ISSUES IDENTIFIED:
{issues}

Provide the fixed code that resolves these issues."""
