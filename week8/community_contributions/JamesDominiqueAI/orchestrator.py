"""
orchestrator.py
---------------
Runs all three research agents in parallel threads, streams their events,
then kicks off the synthesis agent once all three are done.

Resilient: if one or two agents fail, synthesis still runs with the
reports that succeeded.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Generator

from agents.base import AgentEvent, EventType
from agents.anthropic_agent import AnthropicResearchAgent
from agents.openai_agent import OpenAIResearchAgent
from agents.openrouter_agent import OpenRouterResearchAgent
from synthesis_agent import SynthesisAgent

logger = logging.getLogger(__name__)

_SENTINEL = object()


class MultiAgentOrchestrator:
    """
    Orchestrates 3 parallel research agents + 1 synthesis agent.

    Yields (agent_id, AgentEvent):
        agent_id 0 = Claude, 1 = GPT-4o, 2 = Gemini, 3 = Synthesis
    """

    AGENT_CLASSES = [
        AnthropicResearchAgent,
        OpenAIResearchAgent,
        OpenRouterResearchAgent,
    ]

    def __init__(self):
        self._agents    = [cls() for cls in self.AGENT_CLASSES]
        self._synthesis = SynthesisAgent()
        self.synthesis_markdown: str  = ""
        self.synthesis_plain:    str  = ""
        self.agent_markdowns:    list = ["", "", ""]

    def run(self, query: str) -> Generator[tuple[int, AgentEvent], None, None]:
        self.synthesis_markdown = ""
        self.synthesis_plain    = ""
        self.agent_markdowns    = ["", "", ""]

        # ── Phase 1: run 3 agents in parallel ────────────────────────────────
        event_queue: queue.Queue = queue.Queue()

        def run_agent(agent, agent_id: int):
            try:
                for event in agent.run(query):
                    event_queue.put((agent_id, event))
            except Exception as exc:
                logger.exception("Agent %d thread error", agent_id)
                event_queue.put((agent_id, AgentEvent(
                    EventType.ERROR, str(exc), agent_id=agent_id
                )))
            finally:
                event_queue.put((agent_id, _SENTINEL))

        threads = [
            threading.Thread(target=run_agent, args=(agent, i), daemon=True)
            for i, agent in enumerate(self._agents)
        ]
        for t in threads:
            t.start()

        finished: set = set()
        while len(finished) < 3:
            aid, payload = event_queue.get()
            if payload is _SENTINEL:
                finished.add(aid)
                logger.info("Agent %d finished", aid)
            else:
                yield aid, payload

        # ── Collect markdowns — use placeholder for failed agents ─────────────
        succeeded = []
        for i, agent in enumerate(self._agents):
            if agent.success and agent.markdown:
                self.agent_markdowns[i] = agent.markdown
                succeeded.append(i)
            else:
                self.agent_markdowns[i] = f"[Agent {i} did not produce a report: {agent.error}]"
                logger.warning("Agent %d failed — using placeholder for synthesis", i)

        if not succeeded:
            yield 3, AgentEvent(
                EventType.ERROR,
                "All 3 research agents failed — cannot synthesise. Check your API keys and credits.",
                agent_id=3,
            )
            return

        # Inform UI how many agents succeeded
        yield 3, AgentEvent(
            EventType.PLAN,
            f"{len(succeeded)}/3 agents succeeded — proceeding to synthesis…",
            agent_id=3,
        )

        # ── Phase 2: synthesis ────────────────────────────────────────────────
        for event in self._synthesis.run(
            query,
            report_claude=self.agent_markdowns[0],
            report_gpt=self.agent_markdowns[1],
            report_gemini=self.agent_markdowns[2],
        ):
            wait_msg = getattr(self._synthesis, "_last_wait_msg", None)
            if wait_msg:
                yield 3, AgentEvent(EventType.PLAN, wait_msg, agent_id=3)
                self._synthesis._last_wait_msg = None

            yield 3, event

        if self._synthesis.success:
            self.synthesis_markdown = self._synthesis.markdown
            self.synthesis_plain    = self._synthesis.plain_text
