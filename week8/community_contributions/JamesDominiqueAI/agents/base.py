"""
agents/base.py
--------------
Shared base class and AgentEvent types for all research agents.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Generator, Optional


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
    agent_id: int = 0          # 0=Claude, 1=GPT-4o, 2=Gemini, 3=Synthesis
    search_index: int = 0
    timestamp: float = field(default_factory=time.time)

    @property
    def label(self) -> str:
        return self.event_type.name

    def __str__(self) -> str:
        return f"[{self.label}] {self.message}"


EVENT_ICONS = {
    EventType.PLAN:      ("🧠", "PLAN"),
    EventType.SEARCH:    ("🔍", "SEARCH"),
    EventType.RETRIEVED: ("💾", "FETCH"),
    EventType.THINKING:  ("💭", "THINK"),
    EventType.WRITING:   ("✍️",  "WRITE"),
    EventType.COMPLETE:  ("✅", "DONE"),
    EventType.ERROR:     ("❌", "ERROR"),
}


def format_log_line(event: AgentEvent, idx: int) -> str:
    icon, tag = EVENT_ICONS.get(event.event_type, ("•", "INFO"))
    return f"`[{idx:02d}]` {icon} **{tag}** — {event.message}"
