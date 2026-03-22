"""
Analyzer Agent: processes and summarizes content.
"""
from .agent import Agent

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

class AnalyzerAgent(Agent):
    """Analyzes research content and produces key points."""

    name = "Analyzer Agent"
    color = Agent.YELLOW
    MODEL = "gpt-4o-mini"

    def __init__(self, use_llm: bool = False, client=None):
        self.use_llm = use_llm and _OPENAI_AVAILABLE
        self._client = client if client else None
        self.log("Analyzer Agent is ready")

    def analyze(self, content: str) -> str:
        """Return key points or analysis of the given content."""
        self.log("Analyzing content")
        if self.use_llm and self._client:
            try:
                response = self._client.chat.completions.create(
                    model=self.MODEL,
                    messages=[
                        {"role": "system", "content": "Extract 2-3 key points. Be concise."},
                        {"role": "user", "content": content},
                    ],
                    max_tokens=150,
                )
                result = response.choices[0].message.content or ""
                self.log("Analysis complete (LLM)")
                return result.strip()
            except Exception as e:
                self.log(f"LLM fallback: {e}")
        # Mock
        result = f"Key points (mock): 1) Content length: {len(content)} chars. 2) Enable use_llm=True for real analysis."
        self.log("Analysis complete (mock)")
        return result