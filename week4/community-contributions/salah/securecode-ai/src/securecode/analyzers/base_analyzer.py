"""Base analyzer class."""

from openai import OpenAI
from ..config import Config


class BaseAnalyzer:
    """Base class for all analyzers."""

    def __init__(self):
        """Initialize the analyzer with OpenRouter client."""
        Config.validate()
        self.client = OpenAI(
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL,
        )
        self.model = Config.MODEL

    def analyze(self, code: str, language: str = "Python") -> str:
        """Analyze code. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement analyze()")

    def _call_ai(self, system_prompt: str, user_prompt: str, stream: bool = False):
        """Make an API call to the AI model."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=stream,
            temperature=0.3,
        )

        if stream:
            return response
        else:
            return response.choices[0].message.content
