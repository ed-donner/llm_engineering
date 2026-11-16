"""Generate pytest code with the unchanged shipping-fee prompt."""

import argparse
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv
from openai import OpenAI


SPEC = """
Function: shipping_fee(order_total, is_member, express)

Rules:
- order_total must not be negative; otherwise raise ValueError.
- Standard shipping costs 80.
- Standard shipping is free when order_total is at least 1000.
- Standard shipping is also free for members.
- Express shipping adds 120 to whatever the standard shipping fee is.
- The function returns the final shipping fee as an integer.
"""

INSTRUCTIONS = """
You are an expert Python testing engineer.

Generate a pytest test suite for the provided Python function.

The tests must:
- test the documented behaviour thoroughly,
- include important boundary and edge cases,
- import shipping_fee from solution,
- contain only valid Python pytest code.

Return only the Python code. Do not use Markdown code fences.
"""


@dataclass(frozen=True)
class GenerationMetadata:
    model: str
    reasoning_effort: str
    latency_seconds: float
    input_tokens: int | None
    output_tokens: int | None
    reasoning_tokens: int | None
    total_tokens: int | None
    response_id: str | None
    response_model: str | None
    status: str | None
    incomplete_reason: str | None


@dataclass(frozen=True)
class GenerationResult:
    test_code: str
    metadata: GenerationMetadata


class GenerationError(RuntimeError):
    """Keep metadata and partial output when generation is unusable."""

    def __init__(self, message: str, result: GenerationResult):
        super().__init__(message)
        self.result = result


def generate_tests(
    specification: str,
    source_code: str,
    model: str = "gpt-6-luna",
    reasoning_effort: str = "low",
    *,
    client: OpenAI | None = None,
) -> GenerationResult:
    """Return code and API usage; importing this module never calls OpenAI.

    An optional existing client lets callers reuse a connection and lets tests
    supply a fake response without a paid API request.
    """
    if client is None:
        load_dotenv(Path(__file__).with_name(".env"))
        with OpenAI() as api_client:
            return generate_tests(
                specification, source_code, model, reasoning_effort,
                client=api_client,
            )

    started = perf_counter()
    response = client.responses.create(
        model=model,
        reasoning={"effort": reasoning_effort},
        instructions=INSTRUCTIONS,
        input=f"""
REQUIREMENTS:

{specification}

IMPLEMENTATION:

{source_code}

""",
        max_output_tokens=2500,
    )
    latency = perf_counter() - started
    usage = response.usage
    output_details = getattr(usage, "output_tokens_details", None)
    result = GenerationResult(
        test_code=response.output_text,
        metadata=GenerationMetadata(
            model=model,
            reasoning_effort=reasoning_effort,
            latency_seconds=latency,
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
            reasoning_tokens=getattr(output_details, "reasoning_tokens", None),
            total_tokens=getattr(usage, "total_tokens", None),
            response_id=response.id,
            response_model=response.model,
            status=response.status,
            incomplete_reason=getattr(response.incomplete_details, "reason", None),
        ),
    )
    if response.status != "completed" or not result.test_code.strip():
        reason = result.metadata.incomplete_reason or (
            "empty output" if not result.test_code.strip() else "non-completed response"
        )
        raise GenerationError(
            f"Generation did not produce a complete suite: "
            f"{response.status} ({reason}).",
            result,
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--reasoning-effort", default="low")
    args = parser.parse_args()
    source = Path(__file__).with_name("solution.py").read_text(encoding="utf-8")
    print(generate_tests(SPEC, source, args.model, args.reasoning_effort).test_code)


if __name__ == "__main__":
    main()
