"""
Coordinator: orchestrates Researcher -> Analyzer -> Reporter (based on week8 PlanningAgent).
"""
import logging
from agents.agent import Agent
from agents.researcher_agent import ResearcherAgent
from agents.analyzer_agent import AnalyzerAgent
from agents.reporter_agent import ReporterAgent


def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [Multi-Agent] %(message)s",
        datefmt="%H:%M:%S",
    )


class CoordinatorAgent(Agent):
    """Orchestrates the research pipeline: research -> analyze -> report."""

    name = "Coordinator"
    color = Agent.GREEN

    def __init__(self, use_llm: bool = False):
        init_logging()
        self.log("Initializing multi-agent pipeline")
        self.researcher = ResearcherAgent(use_llm=use_llm)
        self.analyzer = AnalyzerAgent(use_llm=use_llm)
        self.reporter = ReporterAgent()
        self.log("Pipeline ready")

    def run(self, topic: str = "multi-agent systems") -> str:
        """Run the full pipeline and return the final report."""
        self.log("Starting pipeline")
        research = self.researcher.research(topic)
        analysis = self.analyzer.analyze(research)
        report = self.reporter.report(topic, research, analysis)
        self.log("Pipeline complete")
        return report
