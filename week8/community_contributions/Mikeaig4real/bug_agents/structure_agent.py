"""
BugStructureAgent — takes analysis results and produces a complete JSON entry
matching the buggy_dataset_nl.jsonl schema using an OpenRouter frontier model.

Uses the OpenAI SDK pointed at OpenRouter (same pattern as Week 8 ScannerAgent).
"""

import os
import json
from typing import Optional
from datetime import datetime
from openai import OpenAI
from bug_agents.agent import Agent
from bug_agents.models import ScrapedBug, BugAnalysis, BugEntry


class BugStructureAgent(Agent):
    """Structures bug analysis into final dataset JSON entries."""

    name = "Bug Structure Agent"
    color = Agent.YELLOW

    MODEL = "openai/gpt-4o"

    SYSTEM_PROMPT = """You are a data structuring assistant.
You receive a buggy Python code snippet, its corrected version, and an analysis of its bugs.
Your job is to produce a clean, well-structured JSON entry for a bug dataset.

The JSON must have EXACTLY these fields:
{
    "level": "easy|medium|hard",
    "description": "brief description of what the code does",
    "buggy_code": "the original buggy code exactly as provided",
    "correct_code": "the corrected code exactly as provided",
    "bug_types": ["list", "of", "bug", "types"],
    "num_bugs": 2,
    "bugs_detail": [
        {"line": 4, "type": "NameError", "description": "..."}
    ],
    "tags": ["topic", "tags"]
}

Rules:
- The description should be a short phrase like "calculates the average of a list"
- The buggy_code must be the EXACT buggy code provided, do not modify it
- The correct_code must be the EXACT corrected code provided, do not modify it
- bug_types should match the types in bugs_detail
- tags should be relevant topic categories (e.g., string, array, math, sorting, recursion, graph)
- Respond ONLY with valid JSON, no explanation"""

    def __init__(self):
        self.log("Bug Structure Agent is initializing")
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openai = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.log("Bug Structure Agent is ready")

    def structure(
        self,
        bug: ScrapedBug,
        analysis: BugAnalysis,
        correct_code: str,
        entry_id: int = 0,
    ) -> Optional[BugEntry]:
        """
        Produce a complete BugEntry from a ScrapedBug + BugAnalysis + Corrected Code.
        Uses OpenAI SDK with structured output (response_format).
        """
        self.log(f"Structuring entry for: {bug.title[:50]}...")

        prompt = f"""Here is a buggy Python code snippet:

```python
{bug.code}
```

Corrected Python code snippet:
```python
{correct_code}
```

Analysis results:
- Description: {analysis.description}
- Number of bugs: {analysis.num_bugs}
- Bug types: {json.dumps(analysis.bug_types)}
- Difficulty: {analysis.level}
- Bug details: {json.dumps([d.model_dump() for d in analysis.bugs_detail])}
- Tags: {json.dumps(analysis.tags)}

Produce the final structured JSON entry. The buggy_code field must contain the EXACT code above."""

        try:
            result = self.openai.beta.chat.completions.parse(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format=BugEntry,
            )
            entry = result.choices[0].message.parsed

            if entry:
                # Ensure buggy_code and correct_code match original string and set metadata
                entry.buggy_code = bug.code
                entry.correct_code = correct_code
                entry.model = f"openrouter/{self.MODEL}"
                entry.id = entry_id
                entry.created_at = datetime.now().isoformat()
                entry.source_url = bug.url
                self.log(f"  ✓ Structured entry #{entry_id}")
                return entry
            else:
                self.log("  ✗ Empty parsed result, using fallback")
                return self._build_fallback(bug, analysis, correct_code, entry_id)

        except Exception as e:
            self.log(f"  Parse error: {e}, using fallback")
            return self._build_fallback(bug, analysis, correct_code, entry_id)

    def _build_fallback(
        self,
        bug: ScrapedBug,
        analysis: BugAnalysis,
        correct_code: str,
        entry_id: int,
    ) -> BugEntry:
        """Build entry directly from analysis when LLM structuring fails."""
        return BugEntry(
            level=analysis.level,
            description=analysis.description,
            buggy_code=bug.code,
            correct_code=correct_code,
            bug_types=analysis.bug_types,
            num_bugs=analysis.num_bugs,
            bugs_detail=analysis.bugs_detail,
            tags=analysis.tags,
            model=f"openrouter/{self.MODEL}",
            id=entry_id,
            created_at=datetime.now().isoformat(),
            source_url=bug.url,
        )
