"""
report.py
---------
Parses the structured report from the agent's raw text output and
converts it into clean Markdown for display in Gradio.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field
from typing import Optional


# ── Data Model  ────────────────────────────────────────────────────────────────

@dataclass
class ResearchReport:
    title: str = "Research Report"
    summary: str = ""
    findings: list[str] = field(default_factory=list)
    analysis: str = ""
    conclusion: str = ""
    sources: list[str] = field(default_factory=list)
    raw_text: str = ""
    is_parsed: bool = False

    # ── Derived properties ────────────────────────────────────────────────────

    @property
    def source_count(self) -> int:
        return len(self.sources)

    @property
    def finding_count(self) -> int:
        return len(self.findings)


# ── Parser ────────────────────────────────────────────────────────────────────

class ReportParser:
    """Extracts structured fields from the agent's delimited report block."""

    def __init__(self, delimiter_start: str, delimiter_end: str):
        self._start = re.escape(delimiter_start)
        self._end = re.escape(delimiter_end)

    def parse(self, text: str) -> ResearchReport:
        report = ResearchReport(raw_text=text)

        # Extract the delimited block
        block_match = re.search(
            rf"{self._start}([\s\S]*?){self._end}", text
        )
        if not block_match:
            # Fallback: return the full text un-parsed
            report.title = "Research Report"
            report.summary = "Report generated — see full text below."
            report.analysis = text
            return report

        block = block_match.group(1)
        report.is_parsed = True

        report.title    = self._field(block, "TITLE",    next_field="SUMMARY")
        report.summary  = self._field(block, "SUMMARY",  next_field="FINDINGS")
        report.findings = self._bullet_list(block, "FINDINGS", next_field="ANALYSIS")
        report.analysis = self._field(block, "ANALYSIS", next_field="CONCLUSION")
        report.conclusion = self._field(block, "CONCLUSION", next_field="SOURCES")
        report.sources  = self._bullet_list(block, "SOURCES", next_field=None)

        return report

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _field(block: str, key: str, next_field: Optional[str]) -> str:
        if next_field:
            pattern = rf"{key}:\s*([\s\S]*?)(?={next_field}:|$)"
        else:
            pattern = rf"{key}:\s*([\s\S]*)$"
        m = re.search(pattern, block)
        return m.group(1).strip() if m else ""

    @staticmethod
    def _bullet_list(block: str, key: str, next_field: Optional[str]) -> list[str]:
        if next_field:
            pattern = rf"{key}:([\s\S]*?)(?={next_field}:|$)"
        else:
            pattern = rf"{key}:([\s\S]*)$"
        m = re.search(pattern, block)
        if not m:
            return []
        raw = m.group(1)
        items = re.findall(r"^[-*•]\s*(.+)", raw, re.MULTILINE)
        return [i.strip() for i in items if i.strip()]


# ── Markdown Renderer ─────────────────────────────────────────────────────────

class MarkdownRenderer:
    """Converts a ResearchReport into nicely formatted Markdown."""

    def render(self, report: ResearchReport) -> str:
        parts: list[str] = []

        # Title
        parts.append(f"# {report.title}\n")

        # Executive Summary
        if report.summary:
            parts.append("## Executive Summary\n")
            parts.append(f"{report.summary}\n")

        # Key Findings
        if report.findings:
            parts.append("## Key Findings\n")
            for i, finding in enumerate(report.findings, 1):
                parts.append(f"**{i}.** {finding}")
            parts.append("")

        # Detailed Analysis
        if report.analysis:
            parts.append("## Detailed Analysis\n")
            # Preserve paragraph breaks
            for para in re.split(r"\n{2,}", report.analysis):
                para = para.strip()
                if para:
                    parts.append(f"{para}\n")

        # Conclusion
        if report.conclusion:
            parts.append("## Conclusion\n")
            for para in re.split(r"\n{2,}", report.conclusion):
                para = para.strip()
                if para:
                    parts.append(f"{para}\n")

        # Sources
        if report.sources:
            parts.append("## Sources Consulted\n")
            for src in report.sources:
                parts.append(f"- {src}")
            parts.append("")

        # Metadata footer
        parts.append("---")
        parts.append(
            f"*{report.finding_count} key findings · "
            f"{report.source_count} sources consulted*"
        )

        return "\n".join(parts)

    def render_raw_fallback(self, report: ResearchReport) -> str:
        """Used when full parsing fails."""
        return f"# {report.title}\n\n{report.raw_text}"


# ── Plain-text export ─────────────────────────────────────────────────────────

def report_to_plain_text(report: ResearchReport) -> str:
    """Export report as a plain .txt string (for download button)."""
    lines = [
        report.title.upper(),
        "=" * len(report.title),
        "",
        "EXECUTIVE SUMMARY",
        "-" * 18,
        textwrap.fill(report.summary, width=80),
        "",
        "KEY FINDINGS",
        "-" * 12,
    ]
    for i, f in enumerate(report.findings, 1):
        lines.append(f"{i}. {textwrap.fill(f, width=78, subsequent_indent='   ')}")
    lines += [
        "",
        "ANALYSIS",
        "-" * 8,
        textwrap.fill(report.analysis.replace("\n\n", "\n"), width=80),
        "",
        "CONCLUSION",
        "-" * 10,
        textwrap.fill(report.conclusion, width=80),
        "",
        "SOURCES",
        "-" * 7,
    ]
    for src in report.sources:
        lines.append(f"  • {src}")
    return "\n".join(lines)
