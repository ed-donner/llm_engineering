"""
Modal deployment for tope-ai-labs simple multi-agent (week8).

Deploy:
  cd week8 && modal deploy community_contributions/tope-ai-labs/week8/modal_multi_agent.py

Run from Python:
  import modal
  Pipeline = modal.Cls.lookup("tope-ai-labs-multi-agent", "MultiAgentPipeline")
  report = Pipeline().run.remote("multi-agent systems")
"""

import modal

APP_NAME = "tope-ai-labs-multi-agent"
CLASS_NAME = "MultiAgentPipeline"

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("openai")
)
# Create a Modal secret named "openai-api-key" with OPENAI_API_KEY (see README)
secrets = [modal.Secret.from_name("openai-api-key", required=False)]

app = modal.App(APP_NAME, image=image)


@app.cls(
    image=image,
    secrets=secrets,
    timeout=120,
)
class MultiAgentPipeline:
    """Runs Researcher -> Analyzer -> Reporter on Modal with OpenAI."""

    @modal.enter()
    def setup(self):
        from openai import OpenAI
        self._client = OpenAI()
        self._model = "gpt-4o-mini"

    def _research(self, topic: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "You briefly research and summarize the topic in 2-4 sentences."},
                {"role": "user", "content": f"Summarize: {topic}"},
            ],
            max_tokens=200,
        )
        return (response.choices[0].message.content or "").strip()

    def _analyze(self, content: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "Extract 2-3 key points. Be concise."},
                {"role": "user", "content": content},
            ],
            max_tokens=150,
        )
        return (response.choices[0].message.content or "").strip()

    def _report(self, topic: str, research: str, analysis: str) -> str:
        lines = [
            "=" * 50,
            f"Report: {topic}",
            "=" * 50,
            "Research:",
            research,
            "",
            "Key points:",
            analysis,
            "=" * 50,
        ]
        return "\n".join(lines)

    @modal.method()
    def run(self, topic: str) -> str:
        """Run the full pipeline: research -> analyze -> report."""
        research = self._research(topic)
        analysis = self._analyze(research)
        return self._report(topic, research, analysis)
