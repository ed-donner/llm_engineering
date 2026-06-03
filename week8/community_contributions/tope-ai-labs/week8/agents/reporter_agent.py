"""
Reporter Agent: formats and delivers the final output (based on week8 MessagingAgent pattern).
"""
from .agent import Agent


class ReporterAgent(Agent):
    """Formats analysis into a final report."""

    name = "Reporter Agent"
    color = Agent.WHITE

    def __init__(self):
        self.log("Reporter Agent is ready")

    def report(self, topic: str, research: str, analysis: str) -> str:
        """Format topic, research, and analysis into a single report string."""
        self.log("Formatting report")
        report = [
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
        out = "\n".join(report)
        self.log("Report ready")
        return out
