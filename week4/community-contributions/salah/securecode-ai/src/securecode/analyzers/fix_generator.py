"""Code fix generator."""

from .base_analyzer import BaseAnalyzer
from ..prompts.fix_prompts import FIX_SYSTEM_PROMPT, get_fix_user_prompt


class FixGenerator(BaseAnalyzer):
    """Generates fixed code based on identified issues."""

    def generate_fix(self, code: str, issues: str, language: str = "Python") -> str:
        """
        Generate fixed code.

        Args:
            code: Original source code
            issues: Identified issues (from security or performance analysis)
            language: Programming language (default: Python)

        Returns:
            Fixed code with explanation
        """
        if not code.strip():
            return "Please provide code to fix."

        if not issues.strip() or "No" in issues[:50]:
            return "No issues identified. Code looks good!"

        user_prompt = get_fix_user_prompt(code, issues, language)
        result = self._call_ai(FIX_SYSTEM_PROMPT, user_prompt)

        # Clean up markdown code blocks if present
        if "```" in result:
            # Extract code block
            parts = result.split("```")
            if len(parts) >= 3:
                return result
        return result

    def generate_fix_stream(self, code: str, issues: str, language: str = "Python"):
        """
        Generate fixed code with streaming response.

        Args:
            code: Original source code
            issues: Identified issues
            language: Programming language (default: Python)

        Yields:
            Chunks of the fixed code and explanation
        """
        if not code.strip():
            yield "Please provide code to fix."
            return

        if not issues.strip() or "No" in issues[:50]:
            yield "No issues identified. Code looks good!"
            return

        user_prompt = get_fix_user_prompt(code, issues, language)
        response = self._call_ai(FIX_SYSTEM_PROMPT, user_prompt, stream=True)

        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
