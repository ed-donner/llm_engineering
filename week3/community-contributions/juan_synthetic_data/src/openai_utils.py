import json
import re
import tempfile
import openai
import pandas as pd

import os
from typing import List


# ------------------ JSON Cleaning ------------------
def _clean_json_output(raw_text: str) -> str:
    """
    Cleans raw OpenAI output to produce valid JSON.
    Escapes only double quotes and control characters.
    """
    text = raw_text.strip()
    text = re.sub(r"```(?:json)?", "", text)
    text = re.sub(r"</?[^>]+>", "", text)

    def escape_quotes(match):
        value = match.group(1)
        value = value.replace('"', r"\"")
        value = value.replace("\n", r"\n").replace("\r", r"\r").replace("\t", r"\t")
        return f'"{value}"'

    text = re.sub(r'"(.*?)"', escape_quotes, text)

    if not text.startswith("["):
        text = "[" + text
    if not text.endswith("]"):
        text += "]"
    text = re.sub(r",\s*]", "]", text)
    return text


# ------------------ Synthetic Data Generation ------------------
def generate_synthetic_data_openai(
    system_prompt: str,
    full_user_prompt: str,
    openai_model: str = "gpt-4o-mini",
    max_tokens: int = 16000,
    temperature: float = 0.0,
):
    """
    Generates synthetic tabular data using OpenAI.
    Assumes `full_user_prompt` is already complete with reference data.
    """
    response = openai.chat.completions.create(
        model=openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_user_prompt},
        ],
        max_completion_tokens=max_tokens,
        temperature=temperature,
    )

    raw_text = response.choices[0].message.content
    cleaned_json = _clean_json_output(raw_text)

    try:
        data = json.loads(cleaned_json)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON generated. Error: {e}\nTruncated output: {cleaned_json[:500]}"
        )

    df = pd.DataFrame(data)

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    df.to_csv(tmp_file.name, index=False)
    tmp_file.close()

    return df, tmp_file.name

# ----------------------Mini call to detect the number of rows in the prompt--------------
def detect_total_rows_from_prompt(user_prompt: str, openai_model: str = "gpt-4o-mini") -> int:
    """
    Detect the number of rows requested from the user prompt.
    Fallback to 20 if detection fails.
    """
    mini_prompt = f"""
    Extract the number of rows to generate from this instruction:
    \"\"\"{user_prompt}\"\"\" Return only the number.
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        response = openai.chat.completions.create(
            model=openai_model,
            messages=[{"role": "user", "content": mini_prompt}],
            temperature=0,
            max_tokens=10,
        )
        text = response.choices[0].message.content.strip()
        total_rows = int("".join(filter(str.isdigit, text)))
        return max(total_rows, 1)
    except Exception:
        return 20


# -------------- Function to generate synthetic data in a batch ---------------------
def generate_batch(system_prompt: str, user_prompt: str, reference_sample: List[dict],
                   batch_size: int, openai_model: str):
    """Generate a single batch of synthetic data using OpenAI."""
    full_prompt = f"{user_prompt}\nSample: {reference_sample}\nGenerate exactly {batch_size} rows."
    df_batch, _ = generate_synthetic_data_openai(
        system_prompt=system_prompt,
        full_user_prompt=full_prompt,
        openai_model=openai_model,
    )
    return df_batch
