import os
from typing import Optional
from openai import OpenAI

from .agent import Agent
from .models import ScrapedBug, BugAnalysis, BugCorrection


class CodeCorrectionAgent(Agent):
    """Generates the corrected version of a buggy Python script."""

    name = "Code Correction Agent"
    color = Agent.GREEN

    # Recommended to use a highly capable model for code generation
    MODEL = "openai/gpt-4o"

    SYSTEM_PROMPT = """You are an expert Python developer.
You receive a buggy Python code snippet and an analysis of its bugs.
Your job is to provide the corrected Python code exactly as requested, fixing all the identified bugs while preserving the original intent and functionality.

Rules:
- Include ONLY the corrected code in your response
- Make sure the corrected code is properly formatted
- Do NOT include any markdown formatting or explanation in the output field, just the raw code text
"""

    def __init__(self):
        self.log("Code Correction Agent is initializing")
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openai = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.log("Code Correction Agent is ready")

    def correct(
        self,
        bug: ScrapedBug,
        analysis: BugAnalysis,
    ) -> Optional[str]:
        """
        Produce a corrected version of the code given the original Code and the Analysis.
        """
        self.log(f"Correcting code for: {bug.title[:50]}...")

        prompt = f"""Here is the buggy Python code snippet:

```python
{bug.code}
```

Analysis results:
- Description: {analysis.description}
- Number of bugs: {analysis.num_bugs}
- Bug types: {", ".join(analysis.bug_types)}
- Difficulty: {analysis.level}

Generate the corrected code snippet that fixes all the bugs mentioned."""

        try:
            result = self.openai.beta.chat.completions.parse(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format=BugCorrection,
            )
            correction = result.choices[0].message.parsed

            if correction and correction.correct_code:
                self.log("  ✓ Code corrected successfully")
                return correction.correct_code
            else:
                self.log("  ✗ Empty parsed result")
                return None

        except Exception as e:
            self.log(f"  ✗ Error during code correction: {e}")
            return None
