"""
BugReportAgent — generates markdown reports and saves JSON entries.
Mirrors week8 MessengerAgent (Pushover notifications).
"""

import json
from pathlib import Path
from typing import List
from bug_agents.agent import Agent
from bug_agents.models import BugEntry, BugReport


class BugReportAgent(Agent):
    """Generates markdown reports and saves structured bug entries."""

    name = "Bug Report Agent"
    color = Agent.MAGENTA

    def __init__(self, output_path: str = "new_bugs.jsonl"):
        self.log("Bug Report Agent is initializing")
        self.output_path = output_path
        self.reports: List[BugReport] = []
        self.log("Bug Report Agent is ready")

    def _format_markdown(self, entry: BugEntry) -> str:
        """Format a BugEntry as a rich markdown report card."""
        # Difficulty badge
        level_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(
            entry.level, "⚪"
        )

        # Bug type badges
        type_badges = " ".join(f"`{bt}`" for bt in entry.bug_types)

        # Bugs detail list
        bugs_list = ""
        for detail in entry.bugs_detail:
            bugs_list += (
                f"  - **Line {detail.line}** [{detail.type}]: {detail.description}\n"
            )

        # Tag list
        tags = " ".join(f"#{t}" for t in entry.tags)

        return f"""## 🐛 Bug Report #{entry.id}

**{entry.description}**

| Field | Value |
|-------|-------|
| Difficulty | {level_emoji} {entry.level.capitalize()} |
| Bug Count | {entry.num_bugs} |
| Bug Types | {type_badges} |
| Tags | {tags} |
| Source | [Stack Overflow]({entry.source_url or "#"}) |

### Buggy Code
```python
{entry.buggy_code}
```

### Bugs Found
{bugs_list}
---
"""

    def report(self, entry: BugEntry) -> BugReport:
        """Generate a markdown report for a single bug entry."""
        self.log(f"Generating report for entry #{entry.id}...")
        markdown = self._format_markdown(entry)
        report = BugReport(markdown=markdown, entry=entry)
        self.reports.append(report)
        self.log(f"  ✓ Report #{entry.id} ready")
        return report

    def save_entries(self, entries: List[BugEntry]):
        """Append entries to new_bugs.jsonl for dataset accumulation."""
        self.log(f"Saving {len(entries)} entries to {self.output_path}...")
        with open(self.output_path, "a", encoding="utf-8") as f:
            for entry in entries:
                line = entry.model_dump_json()
                f.write(line + "\n")
        self.log(f"  ✓ Saved to {self.output_path}")

    def get_full_report(self) -> str:
        """Get the combined markdown report of all bugs found."""
        if not self.reports:
            return "# 🐛 Bug Hunter Report\n\nNo bugs found in this scan."

        header = f"# 🐛 Bug Hunter Report\n\n**{len(self.reports)} bugs analyzed**\n\n---\n\n"
        body = "\n".join(r.markdown for r in self.reports)
        return header + body

    def get_entries_json(self) -> str:
        """Get all entries as a single JSON-lines string."""
        if not self.reports:
            return ""
        lines = [r.entry.model_dump_json() for r in self.reports]
        return "\n".join(lines)
