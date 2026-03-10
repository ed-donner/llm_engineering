"""
agents/openrouter_agent.py
---------------------------
Gemini research agent via OpenRouter — fully agentic loop with live web search.

OpenRouter exposes an OpenAI-compatible API, so we use the same function-calling
pattern as the GPT-4o agent. DuckDuckGo handles the actual search execution.

Architecture:
    User query
        ↓
    Gemini decides what to search  (tool_choice="required" on first call)
        ↓
    DuckDuckGo executes the search
        ↓
    Results fed back into conversation
        ↓
    Loop repeats until Gemini has searched enough
        ↓
    Gemini writes final structured report
"""

from __future__ import annotations

import logging
import time
from typing import Generator

from openai import OpenAI

from agents.base import AgentEvent, EventType
from agents.search import ALL_TOOLS, parse_tool_calls, build_tool_result_messages
from config import config, RESEARCH_PROMPT
from report import ReportParser, MarkdownRenderer, ResearchReport

logger = logging.getLogger(__name__)

AGENT_ID    = 2
MIN_SEARCHES = 4

# OpenRouter extra headers required by their ToS
EXTRA_HEADERS = {
    "HTTP-Referer": "https://research-agent.local",
    "X-Title":      "Multi-Agent Research System",
}


class OpenRouterResearchAgent:
    """
    Gemini research agent via OpenRouter with agentic tool-calling loop.
    Uses DuckDuckGo for real web searches — no extra API key needed.
    """

    name        = "Gemini (OpenRouter)"
    model_label = "gemini-2.0-flash"
    agent_id    = AGENT_ID

    def __init__(self):
        self._client = OpenAI(
            api_key=config.openrouter_api_key,
            base_url=config.openrouter_base_url,
        )
        self._parser   = ReportParser(config.report_delimiter_start, config.report_delimiter_end)
        self._renderer = MarkdownRenderer()
        self.report:   ResearchReport | None = None
        self.markdown: str  = ""
        self.success:  bool = False
        self.error:    str  = ""

    def run(self, query: str) -> Generator[AgentEvent, None, None]:
        self.report   = None
        self.markdown = ""
        self.success  = False
        self.error    = ""

        def ev(etype, msg, **kw):
            return AgentEvent(etype, msg, agent_id=AGENT_ID, **kw)

        t0 = time.time()

        try:
            yield ev(EventType.PLAN, "Formulating multi-angle search strategy…")

            messages = [
                {"role": "system", "content": RESEARCH_PROMPT},
                {"role": "user",   "content": query},
            ]
            all_text: list[str] = []
            search_count = 0
            iterations   = 0

            while iterations < config.max_iterations:
                tool_choice = "required" if iterations == 0 else "auto"

                response = self._client.chat.completions.create(
                    model=config.openrouter_model,
                    max_tokens=config.max_tokens,
                    messages=messages,
                    tools=ALL_TOOLS,
                    tool_choice=tool_choice,
                    extra_headers=EXTRA_HEADERS,
                )

                msg         = response.choices[0].message
                stop_reason = response.choices[0].finish_reason
                tool_calls  = parse_tool_calls(msg)

                logger.info("[Gemini] iter=%d stop=%s tool_calls=%d",
                            iterations, stop_reason, len(tool_calls))

                # Append assistant message to history
                messages.append(msg.model_dump(exclude_unset=True))

                # Execute tool calls
                if tool_calls:
                    tool_results = build_tool_result_messages(tool_calls)
                    for tc, tr in zip(tool_calls, tool_results):
                        search_count += 1
                        yield ev(EventType.SEARCH,
                                 f'Searching: "{tc["args"].get("query", "")}"',
                                 search_index=search_count)
                        yield ev(EventType.RETRIEVED,
                                 f"Results ingested ({len(tr['content'])} chars)")
                    messages.extend(tool_results)

                # Collect text output
                if msg.content:
                    all_text.append(msg.content)
                    # Only show thinking snippet if it is not the final report
                    is_report = config.report_delimiter_start in msg.content
                    if len(msg.content) > 60 and not is_report:
                        yield ev(EventType.THINKING,
                                 msg.content.strip()[:160].replace("\n", " ") + "…")

                # Check completion
                if stop_reason == "stop":
                    if search_count < MIN_SEARCHES:
                        messages.append({
                            "role": "user",
                            "content": (
                                f"You have only searched {search_count} time(s). "
                                f"You MUST search at least {MIN_SEARCHES} times "
                                "before writing the final report. Keep searching."
                            ),
                        })
                        yield ev(EventType.PLAN,
                                 f"Only {search_count} search(es) — requesting more…")
                        iterations += 1
                        continue
                    break

                iterations += 1

            yield ev(EventType.WRITING, "Synthesising findings — writing report…")

            full_text = "\n\n".join(all_text)
            report = self._parser.parse(full_text)
            self.markdown = self._renderer.render(report)
            self.report   = report
            self.success  = True

            elapsed = round(time.time() - t0, 1)
            yield ev(EventType.COMPLETE,
                     f"Done — {search_count} searches, "
                     f"{report.finding_count} findings, {elapsed}s")

        except Exception as exc:
            logger.exception("[Gemini] error")
            self.error = str(exc)
            yield ev(EventType.ERROR, f"Error: {exc}")
