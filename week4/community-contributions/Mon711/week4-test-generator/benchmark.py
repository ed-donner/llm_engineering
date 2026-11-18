"""Generate and evaluate one shipping-fee suite, without changing frozen files."""

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from openai import OpenAI, OpenAIError

from evaluate_mutants import EvaluationResult, evaluate_suite, print_evaluation_summary
from generate_tests import GenerationError, GenerationResult, SPEC, generate_tests


@dataclass(frozen=True)
class BenchmarkResult:
    generation: GenerationResult | None
    evaluation: EvaluationResult


def run_benchmark(
    specification: str,
    source_code: str,
    model: str = "gpt-6-luna",
    reasoning_effort: str = "low",
    *,
    client: OpenAI | None = None,
    timeout_seconds: float = 30,
) -> BenchmarkResult:
    """Connect generation to reference validation and mutation evaluation."""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    generation = generate_tests(
        specification, source_code, model, reasoning_effort, client=client,
    )
    evaluation = evaluate_suite(
        source_code, generation.test_code, timeout_seconds=timeout_seconds,
    )
    return BenchmarkResult(generation, evaluation)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--reasoning-effort", default="low")
    parser.add_argument("--timeout", type=float, default=30, help="Seconds allowed per pytest run")
    parser.add_argument("--tests", type=Path, help="Replay an existing suite without calling OpenAI")
    parser.add_argument("--json", action="store_true", help="Print code, metadata and full evaluation as JSON")
    args = parser.parse_args()
    try:
        source = Path(__file__).with_name("solution.py").read_text(encoding="utf-8")
        if args.tests is not None:
            result = BenchmarkResult(None, evaluate_suite(
                source, args.tests.read_text(encoding="utf-8"), timeout_seconds=args.timeout,
            ))
        else:
            result = run_benchmark(
                SPEC, source, args.model, args.reasoning_effort,
                timeout_seconds=args.timeout,
            )
    except GenerationError as exc:
        if args.json:
            print(json.dumps({"status": "generation_error", "error": str(exc), "generation": asdict(exc.result)}, indent=2))
        else:
            print(f"Generation error: {exc}")
            print(f"Generation metadata: {asdict(exc.result.metadata)}")
        return 1
    except (OpenAIError, OSError, ValueError) as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        else:
            print(f"Benchmark error: {exc}")
        return 1

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        if result.generation is not None:
            metadata = result.generation.metadata
            print(f"Generation: {metadata.model}, effort={metadata.reasoning_effort}, {metadata.latency_seconds:.2f}s")
            print(f"Tokens: input={metadata.input_tokens}, output={metadata.output_tokens}, reasoning={metadata.reasoning_tokens}, total={metadata.total_tokens}")
        else:
            print(f"Existing suite: {args.tests} (no API call)")
        print_evaluation_summary(result.evaluation)
    return 0 if result.evaluation.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
