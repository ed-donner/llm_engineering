"""
BugHunterFramework — orchestrates the full bug hunting pipeline.
Mirrors week8/deal_agent_framework.py (DealAgentFramework).
"""

import os
import requests
import json
import logging
from pathlib import Path
from typing import List
from bug_agents.agent import Agent
from bug_agents.models import BugReport
from bug_agents.scanner_agent import CodeScannerAgent
from bug_agents.analysis_agent import BugAnalysisAgent
from bug_agents.correction_agent import CodeCorrectionAgent
from bug_agents.structure_agent import BugStructureAgent
from bug_agents.report_agent import BugReportAgent


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)


class BugHunterFramework(Agent):
    """
    Orchestrates the multi-agent Bug Hunter pipeline.
    Scan → Analyze → Structure → Report
    """

    name = "Bug Hunter Framework"
    color = Agent.BLUE

    def __init__(
        self,
        dataset_path: str = "buggy_dataset_nl.jsonl",
        db_path: str = "bugs_vectorstore",
        output_path: str = "new_bugs.jsonl",
    ):
        self.log("=" * 60)
        self.log("Bug Hunter Agent Framework starting up...")
        self.log("=" * 60)

        self.dataset_path = dataset_path
        self.memory: List[str] = []  # Previously scanned URLs

        # Initialize agents
        self.scanner = CodeScannerAgent()
        self.analyzer = BugAnalysisAgent(db_path=db_path)
        self.corrector = CodeCorrectionAgent()
        self.structurer = BugStructureAgent()
        self.reporter = BugReportAgent(output_path=output_path)

        # Determine next entry ID from existing dataset
        self.next_id = self._get_max_id() + 1

        self.log("=" * 60)
        self.log("All agents initialized. Ready to hunt bugs!")
        self.log("=" * 60)

    def _get_max_id(self) -> int:
        """Get the maximum ID from the existing dataset."""
        max_id = 0
        path = Path(self.dataset_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            max_id = max(max_id, entry.get("id", 0))
                        except json.JSONDecodeError:
                            continue
        return max_id

    def build_vectorstore(self):
        """Build the Chroma vectorstore from the existing dataset."""
        self.log("Building RAG vectorstore...")
        self.analyzer.build_vectorstore(self.dataset_path)

    def run(self, use_test_data: bool = False) -> List[BugReport]:
        """
        Run the full bug hunting pipeline.

        1. Scan Stack Overflow for buggy code
        2. Analyze each snippet with RAG + frontier model
        3. Correct each snippet using frontier model
        4. Structure into dataset entries
        5. Generate reports and save

        Args:
            use_test_data: If True, use test data instead of hitting SO API

        Returns:
            List of BugReport objects
        """
        self.log("\n" + "=" * 60)
        self.log("Starting Bug Hunt...")
        self.log("=" * 60)

        # Step 1: Scan
        if use_test_data:
            self.log("Using test data (skipping SO API)")
            scraped = self.scanner.test_scan()
        else:
            scraped = self.scanner.scan(memory=self.memory)

        if not scraped:
            self.log("No new bugs found. Ending hunt.")
            return []

        # Step 2: Analyze bugs individually
        self.log(f"Analyzing {len(scraped)} bugs individually...")
        analyses = []
        for bug in scraped:
            analysis = self.analyzer.analyze(bug)
            analyses.append(analysis)

        # Step 3: Correct bugs
        self.log(f"Correcting {len(scraped)} bugs...")
        corrections = []
        for bug, analysis in zip(scraped, analyses):
            if analysis is None:
                corrections.append(None)
                continue
            correction = self.corrector.correct(bug, analysis)
            corrections.append(correction)

        # Step 4: Structure each bug
        entries = []
        for bug, analysis, correction in zip(scraped, analyses, corrections):
            if analysis is None or correction is None:
                self.log(
                    f"  Skipping (analysis or correction failed): {bug.title[:40]}..."
                )
                continue

            # Structure
            entry = self.structurer.structure(
                bug, analysis, correction, entry_id=self.next_id
            )
            if entry is None:
                self.log(f"  Skipping (structuring failed): {bug.title[:40]}...")
                continue

            entries.append(entry)
            self.memory.append(bug.url)
            self.next_id += 1

        # Step 5: Report
        reports = []
        for entry in entries:
            report = self.reporter.report(entry)
            reports.append(report)

        # Save entries
        if entries:
            self.reporter.save_entries(entries)

        # Send Pushover notification
        self.notify_pushover(reports)

        self.log("\n" + "=" * 60)
        self.log(f"Hunt complete! {len(reports)} bugs analyzed and reported.")
        self.log("=" * 60)

        return reports

    def notify_pushover(self, reports: List[BugReport]):
        """Send a Pushover notification with the run summary."""
        user_key = os.getenv("PUSHOVER_USER", "")
        api_token = os.getenv("PUSHOVER_TOKEN", "")

        if not user_key or not api_token:
            self.log(
                "⚠ PUSHOVER_USER or PUSHOVER_TOKEN not set; skipping notification."
            )
            return

        self.log("Sending Pushover notification...")
        try:
            count = len(reports)
            if count == 0:
                message = "Bug Hunter complete! No new bugs found."
            else:
                message = (
                    f"Bug Hunter complete! {count} new bugs found and analyzed:\n\n"
                )
                for i, r in enumerate(reports, 1):
                    # add a short summary of each bug report
                    bug_desc = r.entry.description
                    bug_types = ", ".join(r.entry.bug_types)
                    message += f"{i}. {bug_desc} ({bug_types})\n"

            response = requests.post(
                "https://api.pushover.net/1/messages.json",
                data={
                    "token": api_token,
                    "user": user_key,
                    "message": message,
                    "title": "Bug Hunter Agent",
                },
                timeout=10,
            )
            if response.status_code == 200:
                self.log("  ✓ Notification sent")
            else:
                self.log(f"  ✗ Failed to send notification: {response.text}")
        except Exception as e:
            self.log(f"  ✗ Error sending notification: {e}")

    def get_report_markdown(self) -> str:
        """Get the combined markdown report."""
        return self.reporter.get_full_report()

    def get_entries_json(self) -> str:
        """Get all new entries as JSON-lines."""
        return self.reporter.get_entries_json()
