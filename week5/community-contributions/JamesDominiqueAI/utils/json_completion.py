# utils/json_completion.py
"""
utils/json_completion.py — Cross-provider structured JSON completion.

OpenAI supports response_format=PydanticModel natively.
Anthropic, Gemini, Groq do NOT — they throw an error.

This helper detects which approach to use and falls back to
prompt-based JSON parsing for non-OpenAI providers.
"""

import json
import re
from typing import Type, TypeVar
from pydantic import BaseModel
from litellm import completion

T = TypeVar("T", bound=BaseModel)

# Providers that support response_format=PydanticModel natively
NATIVE_STRUCTURED_OUTPUT_PROVIDERS = {"openai", "azure"}


def _supports_native_structured_output(model: str) -> bool:
    """Check if the model/provider supports response_format=PydanticModel."""
    provider = model.split("/")[0].lower() if "/" in model else "openai"
    return provider in NATIVE_STRUCTURED_OUTPUT_PROVIDERS


def _schema_prompt(schema_class: Type[T]) -> str:
    """Build a JSON instruction block from a Pydantic model's schema."""
    schema = schema_class.model_json_schema()
    return (
        f"\n\nYou MUST respond with valid JSON only — no markdown, no explanation, no code fences. "
        f"The JSON must match this exact schema:\n{json.dumps(schema, indent=2)}"
    )


def _extract_json(text: str) -> str:
    """Strip markdown code fences and extract raw JSON from a response."""
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


def json_completion(
    model: str,
    messages: list,
    schema_class: Type[T],
    **kwargs,
) -> T:
    """
    Call litellm completion and return a validated Pydantic object.

    - For OpenAI: uses response_format=schema_class (native structured output).
    - For all others (Gemini, Anthropic, Groq, etc.): injects the JSON schema
      into the last user message and parses the text response.

    Usage:
        result = json_completion(MODEL, messages, MyPydanticModel)
        # result is a validated MyPydanticModel instance
    """
    if _supports_native_structured_output(model):
        # Native path — OpenAI handles schema enforcement
        response = completion(
            model=model,
            messages=messages,
            response_format=schema_class,
            **kwargs,
        )
        return schema_class.model_validate_json(response.choices[0].message.content)

    else:
        # Fallback path — inject schema into prompt, parse text response
        augmented_messages = list(messages)

        # Append schema instructions to the last user message
        schema_instruction = _schema_prompt(schema_class)
        last = augmented_messages[-1]
        if last["role"] == "user":
            augmented_messages[-1] = {
                "role": "user",
                "content": last["content"] + schema_instruction,
            }
        else:
            # If last message isn't user (e.g. system-only), append as new user turn
            augmented_messages.append({
                "role": "user",
                "content": schema_instruction,
            })

        response = completion(
            model=model,
            messages=augmented_messages,
            **kwargs,
        )
        raw = response.choices[0].message.content
        cleaned = _extract_json(raw)
        return schema_class.model_validate_json(cleaned)
