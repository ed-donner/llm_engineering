"""
Arena orchestration for multi-model LLM comparison.
"""

import asyncio
import os
import time
from functools import lru_cache

from openai import AsyncOpenAI, OpenAIError
from openai.types.chat import ChatCompletionMessageParam


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    base_url = os.environ.get("OPENROUTER_BASE_URL")
    api_key = os.environ.get("OPENROUTER_API_KEY")

    if not base_url or not api_key:
        raise RuntimeError(
            "OPENROUTER_BASE_URL and OPENROUTER_API_KEY must be "
            "set in .env"
        )

    return AsyncOpenAI(base_url=base_url, api_key=api_key)


async def call_model(
    model_id: str, prompt: str, system_prompt: str = ""
) -> dict:
    """Call OpenRouter chat completion for one model.

    Returns a dict with keys ``model``, ``content``, ``tokens``,
    ``elapsed_s``, and ``error``.
    """
    messages: list[ChatCompletionMessageParam] = []

    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    t0 = time.monotonic()

    try:
        response = await _get_client().chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=1024,
        )

        return {
            "model": model_id,
            "content": response.choices[0].message.content,
            "tokens": response.usage.total_tokens if response.usage else None,
            "elapsed_s": round(time.monotonic() - t0, 2),
            "error": None,
        }
    except OpenAIError as e:
        return {
            "model": model_id,
            "content": None,
            "tokens": None,
            "elapsed_s": round(time.monotonic() - t0, 2),
            "error": str(e),
        }


async def run_arena_streaming(
    prompt: str, model_ids: list[str], system_prompt: str = ""
):
    """Yield (model_id, result) tuples as each model finishes."""

    async def _tagged(model_id: str):
        result = await call_model(model_id, prompt, system_prompt)
        return model_id, result

    tasks = [asyncio.create_task(_tagged(mid)) for mid in model_ids]

    for coro in asyncio.as_completed(tasks):
        model_id, result = await coro
        yield model_id, result
