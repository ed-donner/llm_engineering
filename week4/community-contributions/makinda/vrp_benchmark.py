"""
VRP Code-Generation Benchmark — Week 4.

Compares the same LLM providers as Week 3 (OpenRouter, OpenAI, Ollama, Gemini)
on a vehicle routing code-generation task: generate Python that solves the
Nairobi delivery instance and writes vrp_result.json.
"""

import os
import time
from typing import Any, Literal

from dotenv import load_dotenv
from openai import OpenAI

from data_generator import generate_dataset
from evaluator import run_generated_code
from problem_spec import SYSTEM_PROMPT, build_user_prompt
from scoring import compute_score

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Provider config: OpenRouter is used for API access (including OpenAI models).
# Set OPENROUTER_API_KEY in .env; it is used for both "openrouter" and "openai" providers.
# ---------------------------------------------------------------------------

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OLLAMA_BASE_URL = "http://localhost:11434/v1"

# Same model lists as week3/community-contributions/makinda (dataset_generator.py)
MODELS_OPENAI = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4.1-mini",
]
MODELS_OPENROUTER = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3-haiku",
    "mistralai/mistral-7b-instruct",
    "meta-llama/llama-3-8b-instruct",
]
MODELS_OLLAMA = [
    "llama3.2:1b",
    "llama3.2",
    "deepseek-r1:1.5b",
]
MODELS_GEMINI = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

Provider = Literal["openai", "openrouter", "ollama", "gemini"]
PROVIDERS = ["openrouter", "openai", "ollama", "gemini"]


def _openrouter_client() -> OpenAI:
    """Shared OpenRouter client (used for both openrouter and openai providers)."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set in .env (used for OpenRouter and OpenAI models)")
    return OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "http://localhost:7860",
            "X-Title": "VRP Benchmark",
        },
    )


def _get_client(provider: Provider) -> OpenAI:
    if provider in ("openai", "openrouter"):
        return _openrouter_client()
    if provider == "ollama":
        return OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in .env")
        return OpenAI(base_url=GEMINI_BASE_URL, api_key=api_key)
    raise ValueError(f"Unknown provider: {provider}")


def get_models_for_provider(provider: Provider) -> list[str]:
    if provider == "openai":
        return MODELS_OPENAI
    if provider == "openrouter":
        return MODELS_OPENROUTER
    if provider == "ollama":
        return MODELS_OLLAMA
    if provider == "gemini":
        return MODELS_GEMINI
    return []


def run_benchmark(
    provider: Provider,
    model: str,
    n_orders: int = 30,
    window_tightness: Literal["loose", "medium", "tight"] = "medium",
    seed: int | None = 42,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """
    Generate dataset → prompt LLM → execute code → score.
    Returns dict with code, execution result, score, breakdown, and business summary.
    """
    dataset = generate_dataset(
        n_orders=n_orders,
        n_depots=3,
        n_vehicles=12,
        window_tightness=window_tightness,
        seed=seed,
    )
    user_prompt = build_user_prompt(dataset)
    client = _get_client(provider)
    # When using OpenRouter for "openai" provider, send openai/<model_id>
    model_for_api = f"openai/{model}" if provider == "openai" else model
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    gen_start = time.perf_counter()
    response = client.chat.completions.create(
        model=model_for_api,
        messages=messages,
        temperature=0.2,
    )
    gen_time = time.perf_counter() - gen_start
    content = (response.choices[0].message.content or "").strip()
    usage = getattr(response, "usage", None)
    # OpenAI/OpenRouter use prompt_tokens & completion_tokens; some APIs use input_tokens & output_tokens
    if usage is None:
        input_tokens = output_tokens = 0
    else:
        input_tokens = getattr(usage, "prompt_tokens", None) or getattr(usage, "input_tokens", 0)
        output_tokens = getattr(usage, "completion_tokens", None) or getattr(usage, "output_tokens", 0)

    execution = run_generated_code(
        content,
        dataset,
        timeout_seconds=timeout_seconds,
    )
    total_score, breakdown = compute_score(
        execution,
        timeout_seconds=timeout_seconds,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    cost = execution.get("total_cost")
    feasible = execution.get("feasibility", execution.get("feasible", False))
    runtime = execution.get("runtime_seconds")

    # Business-centric summary
    if execution.get("success"):
        if feasible and cost is not None:
            summary = (
                f"Solution is feasible with total operational cost {cost:.2f} KES. "
                f"Runtime {runtime:.1f}s. Score: {total_score:.1f}/100."
            )
        elif not feasible:
            summary = (
                f"Solution violated constraints ({len(execution.get('violations', []))} violations). "
                f"Not suitable for production. Score: {total_score:.1f}/100."
            )
        else:
            summary = f"Code ran but cost or feasibility unclear. Score: {total_score:.1f}/100."
    else:
        summary = (
            f"Execution failed: {execution.get('error', 'unknown')}. "
            f"Model did not produce runnable code or timed out. Score: {total_score:.1f}/100."
        )

    return {
        "code": content,
        "code_gen_seconds": gen_time,
        "execution": execution,
        "total_cost": cost,
        "feasible": feasible,
        "runtime_seconds": runtime,
        "violations": execution.get("violations", []),
        "score": total_score,
        "breakdown": breakdown,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "summary": summary,
    }
