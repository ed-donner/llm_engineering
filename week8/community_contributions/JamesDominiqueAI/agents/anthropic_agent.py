"""
agents/anthropic_agent.py
--------------------------
Research agent using Claude (Anthropic) with live web_search tool.
"""

from __future__ import annotations

import logging
import time
from typing import Generator

import anthropic

from agents.base import AgentEvent, EventType
from config import config, ANTHROPIC_RESEARCH_PROMPT
from memory import ResearchMemory
from report import ReportParser, MarkdownRenderer, report_to_plain_text, ResearchReport
from tools import ALL_TOOLS, build_tool_result_messages, extract_text_blocks, parse_tool_events

logger = logging.getLogger(__name__)

MIN_SEARCHES = 4
AGENT_ID = 0


class AnthropicResearchAgent:
    """Claude-powered research agent with live web search."""

    name = "Claude (Anthropic)"
    model_label = "claude-sonnet-4"
    agent_id = AGENT_ID

    def __init__(self):
        self._client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self._memory = ResearchMemory(config)
        self._parser = ReportParser(config.report_delimiter_start, config.report_delimiter_end)
        self._renderer = MarkdownRenderer()
        self.report: ResearchReport | None = None
        self.markdown: str = ""
        self.success: bool = False
        self.error: str = ""

    def run(self, query: str) -> Generator[AgentEvent, None, None]:
        self.report = None
        self.markdown = ""
        self.success = False
        self.error = ""

        def ev(etype, msg, **kw):
            return AgentEvent(etype, msg, agent_id=AGENT_ID, **kw)

        t0 = time.time()

        try:
            yield ev(EventType.PLAN, f"Query received — formulating search strategy…")
            self._memory.clear()

            messages = [{"role": "user", "content": query}]
            all_text: list[str] = []
            search_count = 0
            iterations = 0

            while iterations < config.max_iterations:
                tool_choice = {"type": "any"} if iterations == 0 else {"type": "auto"}

                response = self._client.messages.create(
                    model=config.anthropic_model,
                    max_tokens=config.max_tokens,
                    system=ANTHROPIC_RESEARCH_PROMPT,
                    tools=ALL_TOOLS,
                    tool_choice=tool_choice,
                    messages=messages,
                )

                content_blocks = [b.model_dump() for b in response.content]
                messages.append({"role": "assistant", "content": content_blocks})

                block_types = ", ".join(
                    f"{b.get('type')}({b.get('name','')})" for b in content_blocks
                )
                logger.info("[Claude] iter=%d blocks=[%s] stop=%s", iterations, block_types, response.stop_reason)

                events = parse_tool_events(content_blocks)
                for evt in events:
                    if evt.is_web_search:
                        search_count += 1
                        yield ev(EventType.SEARCH, f'Searching: "{evt.search_query}"',
                                 search_index=search_count)

                raw_text = extract_text_blocks(content_blocks)
                if raw_text.strip():
                    all_text.append(raw_text)
                    if config.report_delimiter_start not in raw_text:
                        chunks = self._memory.store(raw_text, metadata={"query": query})
                        if chunks:
                            yield ev(EventType.RETRIEVED,
                                     f"Ingested {chunks} chunks ({self._memory.document_count} total)")
                        snippet = raw_text.strip()[:160].replace("\n", " ")
                        if len(snippet) > 60:
                            yield ev(EventType.THINKING, snippet + ("…" if len(raw_text) > 160 else ""))

                if response.stop_reason == "end_turn":
                    if search_count < MIN_SEARCHES:
                        messages.append({"role": "user", "content":
                            f"You have only searched {search_count} time(s). "
                            f"Search at least {MIN_SEARCHES} times before writing the report."})
                        yield ev(EventType.PLAN,
                                 f"Only {search_count} search(es) — requesting more searches…")
                        iterations += 1
                        continue
                    break

                if response.stop_reason == "tool_use":
                    tool_msgs = build_tool_result_messages(content_blocks)
                    if tool_msgs:
                        messages.extend(tool_msgs)

                iterations += 1

            yield ev(EventType.WRITING, "Synthesising findings — writing report…")

            full_text = "\n\n".join(all_text)
            report = self._parser.parse(full_text)
            self.markdown = self._renderer.render(report)
            self.report = report
            self.success = True

            elapsed = round(time.time() - t0, 1)
            yield ev(EventType.COMPLETE,
                     f"Done — {search_count} searches, {report.finding_count} findings, {elapsed}s")

        except anthropic.AuthenticationError:
            self.error = "Authentication failed — check ANTHROPIC_API_KEY."
            yield ev(EventType.ERROR, self.error)
        except Exception as exc:
            logger.exception("[Claude] error")
            self.error = str(exc)
            yield ev(EventType.ERROR, f"Error: {exc}")
