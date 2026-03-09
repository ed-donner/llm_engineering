import json
import math

import pandas as pd

from schemas import DataPoint, SyntheticDataset
from llm_clients import get_client, MODELS
from prompt_builder import build_system_prompt, build_user_prompt

BATCH_SIZE = 5
MIN_COMPLETION_LENGTH = 50


def _call_llm(
    model_key: str, system_prompt: str, user_prompt: str, temperature: float
) -> SyntheticDataset | str:
    """Call the LLM. Returns a SyntheticDataset (OpenAI) or raw JSON string (others)."""
    client, model_name, provider = get_client(model_key)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    if provider == "openai":
        response = client.beta.chat.completions.parse(
            model=model_name,
            messages=messages,
            temperature=temperature,
            response_format=SyntheticDataset,
        )
        return response.choices[0].message.parsed
    else:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content


def _parse_response(raw: SyntheticDataset | str) -> list[DataPoint]:
    """Parse the LLM response into a list of validated DataPoints."""
    if isinstance(raw, SyntheticDataset):
        return raw.data

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []

    items = payload.get("data", [])
    if not isinstance(items, list):
        return []

    datapoints = []
    for item in items:
        try:
            dp = DataPoint(**item)
            datapoints.append(dp)
        except Exception:
            continue
    return datapoints


def _deduplicate(datapoints: list[DataPoint]) -> list[DataPoint]:
    """Remove datapoints with duplicate prompts."""
    seen: set[str] = set()
    unique = []
    for dp in datapoints:
        key = dp.prompt.strip().lower()
        if key not in seen:
            seen.add(key)
            unique.append(dp)
    return unique


def _validate(datapoints: list[DataPoint]) -> list[DataPoint]:
    """Filter out datapoints that don't meet quality thresholds."""
    return [
        dp for dp in datapoints
        if len(dp.completion.strip()) >= MIN_COMPLETION_LENGTH
        and len(dp.prompt.strip()) > 0
        and len(dp.system_prompt.strip()) > 0
    ]


def generate_dataset(
    model_key: str,
    topic: str,
    engineer_level: str,
    dataset_size: int,
    temperature: float = 0.9,
    progress_callback=None,
) -> pd.DataFrame:
    """
    Generate a synthetic dataset by calling the LLM in batches.

    Args:
        model_key: Key from MODELS dict (e.g. "gpt-4.1-mini")
        topic: Domain/topic to focus on
        engineer_level: One of beginner/intermediate/advanced/research
        dataset_size: Target number of datapoints
        temperature: LLM sampling temperature
        progress_callback: Optional callable(current_count, total) for progress updates

    Returns:
        DataFrame with columns: system_prompt, prompt, completion
    """
    all_datapoints: list[DataPoint] = []
    num_batches = math.ceil(dataset_size / BATCH_SIZE)

    for i in range(num_batches):
        remaining = dataset_size - len(all_datapoints)
        if remaining <= 0:
            break

        batch_size = min(BATCH_SIZE, remaining)

        system_prompt = build_system_prompt(topic, engineer_level, batch_size)
        user_prompt = build_user_prompt(topic, engineer_level, batch_size)

        try:
            raw = _call_llm(model_key, system_prompt, user_prompt, temperature)
            batch = _parse_response(raw)
            batch = _validate(batch)
            all_datapoints.extend(batch)
        except Exception as e:
            print(f"Batch {i+1}/{num_batches} failed: {e}")
            continue

        all_datapoints = _deduplicate(all_datapoints)

        if progress_callback:
            progress_callback(len(all_datapoints), dataset_size)

    all_datapoints = all_datapoints[:dataset_size]

    df = pd.DataFrame([dp.model_dump() for dp in all_datapoints])
    return df