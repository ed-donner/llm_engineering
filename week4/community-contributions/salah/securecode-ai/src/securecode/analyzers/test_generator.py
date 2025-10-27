"""Unit test generator."""

from .base_analyzer import BaseAnalyzer
from ..prompts.test_prompts import TEST_SYSTEM_PROMPT, get_test_user_prompt


class TestGenerator(BaseAnalyzer):
    """Generates unit tests for code."""

    def generate_tests(self, code: str, language: str = "Python") -> str:
        """
        Generate unit tests for the provided code.

        Args:
            code: Source code to generate tests for
            language: Programming language (default: Python)

        Returns:
            Generated unit tests
        """
        if not code.strip():
            return "Please provide code to generate tests for."

        user_prompt = get_test_user_prompt(code, language)
        return self._call_ai(TEST_SYSTEM_PROMPT, user_prompt)

    def generate_tests_stream(self, code: str, language: str = "Python"):
        """
        Generate unit tests with streaming response.

        Args:
            code: Source code to generate tests for
            language: Programming language (default: Python)

        Yields:
            Chunks of the generated tests
        """
        if not code.strip():
            yield "Please provide code to generate tests for."
            return

        user_prompt = get_test_user_prompt(code, language)
        response = self._call_ai(TEST_SYSTEM_PROMPT, user_prompt, stream=True)

        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
