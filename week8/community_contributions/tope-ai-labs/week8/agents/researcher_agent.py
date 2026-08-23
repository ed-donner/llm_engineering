"""
Researcher Agent: gathers or simulates input for the pipeline (based on week8 ScannerAgent pattern).
"""
from .agent import Agent

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


class ResearcherAgent(Agent):
    """Fetches or generates a topic summary for the pipeline."""

    name = "Researcher Agent"
    color = Agent.CYAN
    MODEL = "gpt-4o-mini"

    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm and _OPENAI_AVAILABLE
        if self.use_llm:
            self.log("Initializing with OpenAI")
            self._client = OpenAI()
        self.log("Researcher Agent is ready")

    def research(self, topic: str) -> str:
        """Return research content for the given topic (LLM or mock)."""
        self.log(f"Researching topic: {topic}")
        if self.use_llm:
            try:
                response = self._client.chat.completions.create(
                    model=self.MODEL,
                    messages=[
                        {"role": "system", "content": "You briefly research and summarize the topic in 2-4 sentences."},
                        {"role": "user", "content": f"Summarize: {topic}"},
                    ],
                    max_tokens=200,
                )
                content = response.choices[0].message.content or ""
                self.log("Research complete (LLM)")
                return content.strip()
            except Exception as e:
                self.log(f"LLM fallback: {e}")
        # Mock response when no LLM
        mock = (
            f"Research summary for '{topic}': "
            "This is a placeholder. Set use_llm=True and have OPENAI_API_KEY for real research."
        )
        self.log("Research complete (mock)")
        return mock
