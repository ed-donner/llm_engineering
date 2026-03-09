"""
agent.py
--------
Core Research Agent — orchestrates the plan -> search -> retrieve -> report loop.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Generator, Optional

import anthropic

from config import config, SYSTEM_PROMPT
from memory import ResearchMemory
from report import ResearchReport, ReportParser, MarkdownRenderer, report_to_plain_text
from tools import (
    ALL_TOOLS,
    build_tool_result_messages,
    extract_text_blocks,
    parse_tool_events,
)

logger = logging.getLogger(__name__)

MIN_SEARCHES = 4   # minimum web_search calls required before writing the report


# ── Status Events ─────────────────────────────────────────────────────────────

class EventType(Enum):
    PLAN      = auto()
    SEARCH    = auto()
    RETRIEVED = auto()
    THINKING  = auto()
    WRITING   = auto()
    COMPLETE  = auto()
    ERROR     = auto()


@dataclass
class AgentEvent:
    event_type: EventType
    message: str
    search_index: int = 0
    timestamp: float = field(default_factory=time.time)

    @property
    def label(self) -> str:
        return self.event_type.name

    def __str__(self) -> str:
        return f"[{self.label}] {self.message}"


# ── Research Result ────────────────────────────────────────────────────────────

@dataclass
class ResearchResult:
    report: Optional[ResearchReport] = None
    markdown: str = ""
    plain_text: str = ""
    search_count: int = 0
    elapsed_seconds: float = 0.0
    success: bool = False
    error: Optional[str] = None


# ── Agent ──────────────────────────────────────────────────────────────────────

MIN_SEARCHES = 4   # enforce at least this many before accepting end_turn

class ResearchAgent:
    """
    Agentic research loop.

    Usage:
        agent = ResearchAgent()
        for event in agent.run(query):
            print(event)
        result = agent.last_result
    """

    def __init__(self):
        self._client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self._memory = ResearchMemory(config)
        self._parser = ReportParser(
            config.report_delimiter_start, config.report_delimiter_end
        )
        self._renderer = MarkdownRenderer()
        self.last_result: Optional[ResearchResult] = None

    # ── Public ────────────────────────────────────────────────────────────────

    def run(self, query: str) -> Generator[AgentEvent, None, None]:
        """Generator that yields AgentEvents. Sets self.last_result when done."""
        self.last_result = None
        t_start = time.time()
        result = ResearchResult()

        try:
            yield AgentEvent(EventType.PLAN, f'Query received: "{query}"')
            yield AgentEvent(EventType.PLAN, "Formulating multi-angle search strategy...")

            self._memory.clear()

            messages: list[dict] = [{"role": "user", "content": query}]
            all_text_blocks: list[str] = []
            search_count = 0
            iterations = 0

            while iterations < config.max_iterations:
                # On the first iteration force the model to use a tool so it
                # cannot skip straight to writing from training data.
                tool_choice = {"type": "any"} if iterations == 0 else {"type": "auto"}

                response = self._client.messages.create(
                    model=config.model,
                    max_tokens=config.max_tokens,
                    system=SYSTEM_PROMPT,
                    tools=ALL_TOOLS,
                    tool_choice=tool_choice,
                    messages=messages,
                )

                content_blocks = [b.model_dump() for b in response.content]
                messages.append({"role": "assistant", "content": content_blocks})

                # Debug: log block types so we can see what the API returns
                block_summary = ", ".join(
                    f"{b.get('type')}({b.get('name','')})" for b in content_blocks
                )
                logger.info("Iteration %d blocks: [%s] stop=%s", iterations, block_summary, response.stop_reason)

                events = parse_tool_events(content_blocks)

                for evt in events:
                    if evt.is_web_search:
                        search_count += 1
                        yield AgentEvent(
                            EventType.SEARCH,
                            f'Searching: "{evt.search_query}"',
                            search_index=search_count,
                        )

                # Collect and store text
                raw_text = extract_text_blocks(content_blocks)
                if raw_text.strip():
                    all_text_blocks.append(raw_text)
                    if config.report_delimiter_start not in raw_text:
                        chunks_stored = self._memory.store(
                            raw_text,
                            metadata={"query": query, "iteration": iterations},
                        )
                        if chunks_stored:
                            yield AgentEvent(
                                EventType.RETRIEVED,
                                f"Ingested {chunks_stored} chunks into vector memory "
                                f"({self._memory.document_count} total)",
                            )
                        snippet = raw_text.strip()[:180].replace("\n", " ")
                        if len(snippet) > 60:
                            yield AgentEvent(
                                EventType.THINKING,
                                snippet + ("..." if len(raw_text) > 180 else ""),
                            )

                if response.stop_reason == "end_turn":
                    # If we haven't searched enough, push back and demand searches
                    if search_count < MIN_SEARCHES:
                        nudge = (
                            f"You have only searched {search_count} time(s). "
                            f"You MUST search at least {MIN_SEARCHES} times before writing the report. "
                            "Please continue searching now."
                        )
                        messages.append({"role": "user", "content": nudge})
                        yield AgentEvent(
                            EventType.PLAN,
                            f"Only {search_count} search(es) so far — nudging agent to search more...",
                        )
                        iterations += 1
                        continue
                    # Enough searches done — break
                    break

                if response.stop_reason == "tool_use":
                    tool_results = build_tool_result_messages(content_blocks)
                    if tool_results:
                        messages.extend(tool_results)

                iterations += 1

            # ── Retrieve top memory chunks for synthesis context ──────────
            if self._memory.is_ready:
                top_chunks = self._memory.retrieve(query)
                if top_chunks:
                    yield AgentEvent(
                        EventType.RETRIEVED,
                        f"Retrieved {len(top_chunks)} most relevant memory chunks for synthesis",
                    )

            yield AgentEvent(EventType.WRITING, "Synthesising findings — writing intelligence report...")

            full_text = "\n\n".join(all_text_blocks)
            report = self._parser.parse(full_text)
            markdown = self._renderer.render(report)
            plain = report_to_plain_text(report)

            elapsed = round(time.time() - t_start, 1)
            result.report = report
            result.markdown = markdown
            result.plain_text = plain
            result.search_count = search_count
            result.elapsed_seconds = elapsed
            result.success = True
            self.last_result = result  # set BEFORE yielding so app.py can read it

            yield AgentEvent(
                EventType.COMPLETE,
                f"Research complete — {search_count} searches, "
                f"{report.finding_count} findings, "
                f"{report.source_count} sources, "
                f"{elapsed}s elapsed.",
            )

        except anthropic.AuthenticationError:
            msg = "Authentication failed — check your ANTHROPIC_API_KEY."
            result.error = msg
            yield AgentEvent(EventType.ERROR, msg)

        except anthropic.RateLimitError:
            msg = "Rate limit hit — please wait a moment and try again."
            result.error = msg
            yield AgentEvent(EventType.ERROR, msg)

        except Exception as exc:
            msg = f"Unexpected error: {exc}"
            logger.exception("Agent error")
            result.error = msg
            yield AgentEvent(EventType.ERROR, msg)

        self.last_result = result
