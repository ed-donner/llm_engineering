"""Call a judge LLM to score and compare multiple model responses."""

import json
import os
import re
from functools import lru_cache

from openai import AsyncOpenAI, OpenAIError
from src.config import JUDGE_MODEL, JUDGE_SYSTEM_PROMPT


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    base_url = os.environ.get("OPENROUTER_BASE_URL")
    api_key = os.environ.get("OPENROUTER_API_KEY")

    if not base_url or not api_key:
        raise RuntimeError(
            "OPENROUTER_BASE_URL and OPENROUTER_API_KEY must be set in .env"
        )

    return AsyncOpenAI(base_url=base_url, api_key=api_key)


def _parse_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"```(?:\w+)?\s*(\{.*\})\s*```", text, re.DOTALL)

    if m:
        text = m.group(1)

    return json.loads(text)


async def evaluate_responses(
    prompt: str, responses: list[dict], judge_model: str = JUDGE_MODEL,
) -> dict:
    """Score valid replies via the judge LLM; return evaluations and winner."""
    valid = [r for r in responses if r["error"] is None]

    if not valid:
        return {"error": "All models returned errors."}

    if len(valid) == 1:
        return {
            "evaluations": [{
                "model": valid[0]["model"],
                "scores": {
                    "accuracy": 0,
                    "conciseness": 0,
                    "tone": 0,
                    "speed": 0,
                },
                "reasoning": "Only one model responded; no comparison.",
            }],
            "winner": valid[0]["model"],
        }

    eval_content = f"USER PROMPT:\n{prompt}\n\n"

    for r in valid:
        elapsed = r.get("elapsed_s")
        time_info = f" (response time: {elapsed}s)" if elapsed else ""
        eval_content += f"MODEL '{r['model']}'{time_info} RESPONSE:\n"
        eval_content += f"{r['content']}\n\n---\n\n"

    try:
        response = await _get_client().chat.completions.create(
            model=judge_model,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": eval_content},
            ],
            max_tokens=1024,
        )

        raw = response.choices[0].message.content

        if raw is None:
            return {"error": "Judge returned empty content."}

        return _parse_json(raw)
    except json.JSONDecodeError as e:
        return {"error": f"Judge returned invalid JSON: {e}"}
    except OpenAIError as e:
        return {"error": f"Judge call failed: {e}"}
