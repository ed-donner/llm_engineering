from openai import OpenAI
from agents.agent import Agent
from agents.knowledge_agent import KnowledgeAgent
import modal


class AnalysisAgent(Agent):

    name = "Analysis Agent"
    color = Agent.YELLOW
    MODEL = "gpt-4.1-mini"

    def __init__(self, knowledge: KnowledgeAgent):
        self.log("Initializing")
        self.knowledge = knowledge
        self.openai = OpenAI()
        self.modal_scorer = None
        try:
            Scorer = modal.Cls.from_name("newshound-scorer", "Scorer")
            self.modal_scorer = Scorer()
            self.log("Connected to Modal relevance scorer")
        except Exception:
            self.log("Modal scorer not deployed - using LLM-only scoring")

    def _modal_score(self, text: str) -> float:
        if not self.modal_scorer:
            return -1
        try:
            score = self.modal_scorer.score.remote(text)
            self.log(f"Modal relevance score: {score}/10")
            return score
        except Exception as e:
            self.log(f"Modal scorer error: {e}")
            return -1

    def analyze(self, title: str, summary: str, url: str) -> float:
        self.log(f"Analyzing: {title[:50]}...")
        text = f"{title}. {summary}"

        similar = self.knowledge.find_similar(text)
        context_block = ""
        if similar:
            context_block = "\nRelated past stories:\n" + "\n".join(
                f"- {s[:120]}" for s in similar
            )

        modal_score = self._modal_score(text)
        modal_line = (
            f"\nTech relevance score from ML model: {modal_score}/10"
            if modal_score >= 0
            else ""
        )

        prompt = (
            "Rate this tech article's importance from 0 to 10. "
            "Consider novelty, impact, and technical significance. "
            "Respond with just a number.\n\n"
            f"Title: {title}\nSummary: {summary}"
            f"{modal_line}{context_block}\n\nImportance (0-10):"
        )
        response = self.openai.chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            score = float(response.choices[0].message.content.strip().split()[0])
            score = min(10.0, max(0.0, score))
        except (ValueError, IndexError):
            score = max(modal_score, 5.0) if modal_score >= 0 else 5.0

        self.knowledge.add_article(title, summary, url)

        self.log(f"Importance: {score}/10 for '{title[:40]}...'")
        return score
