"""
synthesis_agent.py
------------------
Synthesis agent: combines 3 research reports into one authoritative report.
Uses GPT-4o (OpenAI) — high rate limits, no Anthropic free-tier bottleneck.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Generator, Optional

from openai import OpenAI, RateLimitError as OpenAIRateLimitError

from agents.base import AgentEvent, EventType
from config import config, SYNTHESIS_PROMPT
from report import ReportParser, MarkdownRenderer, ResearchReport

logger = logging.getLogger(__name__)

AGENT_ID        = 3
MAX_REPORT_CHARS = 6_000   # GPT-4o has 128k context — generous budget
SYNTHESIS_MAX_TOKENS = 3_000
MAX_RETRIES      = 3
RETRY_BASE_WAIT  = 30


# ── Extended dataclasses ──────────────────────────────────────────────────────

@dataclass
class SynthesisReport(ResearchReport):
    consensus:     list[str] = field(default_factory=list)
    disagreements: list[str] = field(default_factory=list)


class SynthesisReportParser(ReportParser):
    def parse(self, text: str) -> SynthesisReport:
        base  = super().parse(text)
        synth = SynthesisReport(
            title=base.title, summary=base.summary, findings=base.findings,
            analysis=base.analysis, conclusion=base.conclusion,
            sources=base.sources, raw_text=base.raw_text, is_parsed=base.is_parsed,
        )
        m = re.search(
            rf"{re.escape(config.report_delimiter_start)}([\s\S]*?)"
            rf"{re.escape(config.report_delimiter_end)}", text,
        )
        if m:
            block = m.group(1)
            synth.consensus     = self._bullet_list(block, "CONSENSUS",     next_field="DISAGREEMENTS")
            synth.disagreements = self._bullet_list(block, "DISAGREEMENTS", next_field="FINDINGS")
        return synth


class SynthesisMarkdownRenderer(MarkdownRenderer):
    def render(self, report) -> str:
        if not isinstance(report, SynthesisReport):
            return super().render(report)

        parts = [f"# {report.title}\n"]

        if report.summary:
            parts += ["## Executive Summary\n", f"{report.summary}\n"]

        if report.consensus:
            parts += ["## ✅ Points of Consensus\n"]
            parts += [f"- {i}" for i in report.consensus]
            parts.append("")

        if report.disagreements:
            parts += ["## ⚡ Points of Disagreement\n"]
            parts += [f"- {i}" for i in report.disagreements]
            parts.append("")

        if report.findings:
            parts += ["## Synthesised Key Findings\n"]
            parts += [f"**{i+1}.** {f}" for i, f in enumerate(report.findings)]
            parts.append("")

        if report.analysis:
            parts += ["## Deep Analysis\n"]
            for para in re.split(r"\n{2,}", report.analysis):
                para = para.strip()
                if para:
                    parts.append(f"{para}\n")

        if report.conclusion:
            parts += ["## Final Verdict\n"]
            for para in re.split(r"\n{2,}", report.conclusion):
                para = para.strip()
                if para:
                    parts.append(f"{para}\n")

        if report.sources:
            parts += ["## Combined Sources\n"]
            parts += [f"- {s}" for s in report.sources]
            parts.append("")

        parts += [
            "---",
            f"*Synthesised by GPT-4o from Claude · GPT-4o · Gemini — "
            f"{report.finding_count} findings · {report.source_count} sources*",
        ]
        return "\n".join(parts)


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[… truncated for token budget …]"


# ── Agent ─────────────────────────────────────────────────────────────────────

class SynthesisAgent:
    name        = "Synthesis (GPT-4o)"
    model_label = "gpt-4o"
    agent_id    = AGENT_ID

    def __init__(self):
        self._client   = OpenAI(api_key=config.openai_api_key)
        self._parser   = SynthesisReportParser(
            config.report_delimiter_start, config.report_delimiter_end
        )
        self._renderer = SynthesisMarkdownRenderer()
        self.report:          Optional[SynthesisReport] = None
        self.markdown:        str  = ""
        self.plain_text:      str  = ""
        self.success:         bool = False
        self.error:           str  = ""
        self._last_wait_msg:  Optional[str] = None

    def run(
        self,
        query:         str,
        report_claude: str,
        report_gpt:    str,
        report_gemini: str,
    ) -> Generator[AgentEvent, None, None]:
        # reset
        self.report = self.markdown = self.plain_text = None
        self.markdown = self.plain_text = ""
        self.success = False
        self.error = ""
        self._last_wait_msg = None

        def ev(etype, msg):
            return AgentEvent(etype, msg, agent_id=AGENT_ID)

        t0 = time.time()
        try:
            yield ev(EventType.PLAN,     "All 3 agents complete — GPT-4o synthesis starting…")
            yield ev(EventType.THINKING, "Comparing findings across Claude, GPT-4o, and Gemini…")

            r1 = _truncate(report_claude, MAX_REPORT_CHARS)
            r2 = _truncate(report_gpt,    MAX_REPORT_CHARS)
            r3 = _truncate(report_gemini, MAX_REPORT_CHARS)

            total = len(r1) + len(r2) + len(r3)
            yield ev(EventType.THINKING,
                     f"Input: {total:,} chars (~{total//4:,} tokens) → GPT-4o")

            user_content = (
                f"**Research query:** {query}\n\n"
                f"---\n## REPORT 1 — Claude (Anthropic)\n\n{r1}\n\n"
                f"---\n## REPORT 2 — GPT-4o (OpenAI)\n\n{r2}\n\n"
                f"---\n## REPORT 3 — Gemini (OpenRouter)\n\n{r3}\n\n"
                f"---\nSynthesise all three reports into one authoritative report."
            )

            yield ev(EventType.WRITING, "Calling GPT-4o — writing synthesis…")
            raw_text = self._call_with_retry(user_content)

            if not raw_text.strip():
                raise ValueError("GPT-4o returned an empty response.")

            logger.info("[Synthesis] raw response length: %d chars", len(raw_text))

            report = self._parser.parse(raw_text)
            self.markdown   = self._renderer.render(report)
            self.plain_text = raw_text
            self.report     = report
            self.success    = True   # ← set BEFORE yielding COMPLETE

            elapsed = round(time.time() - t0, 1)
            yield ev(
                EventType.COMPLETE,
                f"Synthesis complete — {report.finding_count} findings, "
                f"{len(report.consensus)} consensus, "
                f"{len(report.disagreements)} disagreements, {elapsed}s",
            )

        except Exception as exc:
            logger.exception("[Synthesis/GPT-4o] error")
            self.error = str(exc)
            yield ev(EventType.ERROR, f"Synthesis error: {exc}")

    def _call_with_retry(self, user_content: str) -> str:
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=SYNTHESIS_MAX_TOKENS,
                    messages=[
                        {"role": "system", "content": SYNTHESIS_PROMPT},
                        {"role": "user",   "content": user_content},
                    ],
                )
                content = response.choices[0].message.content
                logger.info("[Synthesis] GPT-4o finish_reason=%s content_len=%d",
                            response.choices[0].finish_reason,
                            len(content) if content else 0)
                return content or ""

            except OpenAIRateLimitError as exc:
                last_exc = exc
                wait = RETRY_BASE_WAIT * attempt
                logger.warning("[Synthesis] rate limit attempt %d/%d — waiting %ds",
                               attempt, MAX_RETRIES, wait)
                self._last_wait_msg = (
                    f"GPT-4o rate limit (attempt {attempt}/{MAX_RETRIES}) "
                    f"— retrying in {wait}s…"
                )
                time.sleep(wait)

        raise last_exc
