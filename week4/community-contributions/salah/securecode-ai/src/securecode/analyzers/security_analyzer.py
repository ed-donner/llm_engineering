"""Security vulnerability analyzer."""

from .base_analyzer import BaseAnalyzer
from ..prompts.security_prompts import SECURITY_SYSTEM_PROMPT, get_security_user_prompt


class SecurityAnalyzer(BaseAnalyzer):
    """Analyzes code for security vulnerabilities."""

    def analyze(self, code: str, language: str = "Python") -> str:
        """
        Analyze code for security vulnerabilities.

        Args:
            code: Source code to analyze
            language: Programming language (default: Python)

        Returns:
            Security analysis report
        """
        if not code.strip():
            return "Please provide code to analyze."

        user_prompt = get_security_user_prompt(code, language)
        return self._call_ai(SECURITY_SYSTEM_PROMPT, user_prompt)

    def analyze_stream(self, code: str, language: str = "Python"):
        """
        Analyze code with streaming response.

        Args:
            code: Source code to analyze
            language: Programming language (default: Python)

        Yields:
            Chunks of the analysis report
        """
        if not code.strip():
            yield "Please provide code to analyze."
            return

        user_prompt = get_security_user_prompt(code, language)
        response = self._call_ai(SECURITY_SYSTEM_PROMPT, user_prompt, stream=True)

        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
