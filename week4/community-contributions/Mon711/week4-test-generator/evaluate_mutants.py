"""Evaluate the reference implementation before the five existing mutants."""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Literal


mutants = [
    {
        "name": "Threshold excludes exactly 1000",
        "old": "order_total >= 1000",
        "new": "order_total > 1000",
    },
    {
        "name": "Membership no longer gives free shipping",
        "old": "order_total >= 1000 or is_member",
        "new": "order_total >= 1000",
    },
    {
        "name": "Express shipping costs 100 instead of 120",
        "old": "express_fee = 120 if express else 0",
        "new": "express_fee = 100 if express else 0",
    },
    {
        "name": "Zero order total is incorrectly rejected",
        "old": "if order_total < 0:",
        "new": "if order_total <= 0:",
    },
    {
        "name": "Standard shipping costs 60 instead of 80",
        "old": "else 80",
        "new": "else 60",
    },
]


@dataclass(frozen=True)
class PytestResult:
    status: Literal["passed", "failed", "error"]
    returncode: int | None
    latency_seconds: float
    stdout: str = ""
    stderr: str = ""
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    collected: int = 0
    error: str | None = None


@dataclass(frozen=True)
class MutantResult:
    name: str
    status: Literal["killed", "survived", "error", "not_run"]
    pytest: PytestResult | None = None
    error: str | None = None


@dataclass(frozen=True)
class EvaluationResult:
    status: Literal["completed", "invalid", "error"]
    reference_passed: bool
    reference: PytestResult
    mutants_killed: int
    total_mutants: int
    mutation_score: float | None  # Percentage; None means no valid score.
    mutants: list[MutantResult]


def run_pytest(
    source_code: str, test_code: str, *, timeout_seconds: float = 30,
) -> PytestResult:
    """Run one suite in a fresh folder, using this process's Python environment."""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    started = perf_counter()
    try:
        with TemporaryDirectory(prefix="shipping-evaluation-") as directory:
            root = Path(directory)
            (root / "solution.py").write_text(source_code, encoding="utf-8")
            (root / "test_generated.py").write_text(test_code, encoding="utf-8")
            (root / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
            (root / "_pytest_reporter.py").write_text(
                Path(__file__).with_name("_pytest_reporter.py").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            env = os.environ.copy()
            # Keep repository configuration, plugins and imports out of the run.
            for key in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"):
                env.pop(key, None)
            env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--tb=short",
                 "-c", "pytest.ini", "-p", "no:cacheprovider",
                 "-p", "_pytest_reporter", "test_generated.py"],
                cwd=root, env=env, capture_output=True, text=True,
                timeout=timeout_seconds,
            )
            try:
                counts = json.loads((root / "pytest_results.json").read_text(encoding="utf-8"))
                keys = {"passed", "failed", "errors", "skipped", "collected"}
                if (
                    not isinstance(counts, dict)
                    or set(counts) != keys
                    or any(type(v) is not int or v < 0 for v in counts.values())
                ):
                    raise ValueError("invalid test counts")
            except (OSError, ValueError, TypeError) as exc:
                return PytestResult(
                    "error", completed.returncode, perf_counter() - started,
                    completed.stdout, completed.stderr,
                    error=f"Missing or invalid pytest report: {exc}",
                )

            status = "error"
            error = f"Pytest exited with code {completed.returncode}."
            finished = counts["passed"] + counts["failed"] + counts["skipped"]
            all_finished = finished == counts["collected"]
            if (
                completed.returncode == 0 and counts["passed"] > 0
                and not counts["failed"] and not counts["errors"] and all_finished
            ):
                status, error = "passed", None
            elif (
                completed.returncode == 1 and counts["failed"] > 0
                and not counts["errors"] and all_finished
            ):
                status, error = "failed", None
            elif counts["errors"]:
                error = "Pytest encountered collection, setup, teardown or test-runtime errors."
            elif not counts["passed"] and not counts["failed"]:
                error = "No tests executed (the suite was empty or all tests were skipped)."
            elif not all_finished:
                error = "Pytest stopped before every collected test finished."
            return PytestResult(
                status, completed.returncode, perf_counter() - started,
                completed.stdout, completed.stderr, **counts, error=error,
            )
    except subprocess.TimeoutExpired as exc:
        # TimeoutExpired may contain bytes even when text=True.
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout or ""
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr or ""
        return PytestResult(
            "error", None, perf_counter() - started, stdout, stderr,
            error=f"Pytest timed out after {timeout_seconds:g} seconds.",
        )
    except OSError as exc:
        return PytestResult("error", None, perf_counter() - started, error=str(exc))


def evaluate_suite(
    source_code: str, test_code: str, *, timeout_seconds: float = 30,
) -> EvaluationResult:
    """Reject invalid suites; only report a score when every mutant run is valid."""
    reference = run_pytest(source_code, test_code, timeout_seconds=timeout_seconds)
    if reference.status != "passed":
        return EvaluationResult(
            "invalid", False, reference, 0, len(mutants), None,
            [MutantResult(m["name"], "not_run", error="Reference suite did not pass.") for m in mutants],
        )

    results = []
    for mutant in mutants:
        mutant_code = source_code.replace(mutant["old"], mutant["new"])
        if mutant_code == source_code:
            results.append(MutantResult(mutant["name"], "error", error="Could not create mutant: replacement not found."))
            continue
        result = run_pytest(mutant_code, test_code, timeout_seconds=timeout_seconds)
        status = {"passed": "survived", "failed": "killed", "error": "error"}[result.status]
        results.append(MutantResult(mutant["name"], status, result, result.error))

    killed = sum(result.status == "killed" for result in results)
    has_errors = any(result.status == "error" for result in results)
    return EvaluationResult(
        "error" if has_errors else "completed", True, reference,
        killed, len(mutants), None if has_errors else killed / len(mutants) * 100,
        results,
    )


def print_evaluation_summary(result: EvaluationResult) -> None:
    print(f"Reference: {result.reference.status.upper()} ({result.reference.passed} passed)")
    for mutant in result.mutants:
        print(f"{mutant.status.upper():8} {mutant.name}")
    if result.mutation_score is None:
        print(f"Mutation score: unavailable ({result.status}); {result.mutants_killed}/{result.total_mutants} confirmed kills")
    else:
        print(f"Mutation score: {result.mutants_killed}/{result.total_mutants} = {result.mutation_score:.1f}%")
    failures = [("Reference", result.reference)] if not result.reference_passed else []
    failures.extend((m.name, m.pytest) for m in result.mutants if m.status == "error")
    for name, run in failures:
        if run is not None:
            print(f"\n{name}: {run.error or 'Tests failed against the correct implementation.'}")
            print(run.stdout + run.stderr)
        else:
            print(f"\n{name}: mutant could not be created.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tests", type=Path, default=Path(__file__).with_name("test_generated.py"))
    parser.add_argument("--timeout", type=float, default=30, help="Seconds allowed per pytest run")
    args = parser.parse_args()
    source = Path(__file__).with_name("solution.py").read_text(encoding="utf-8")
    result = evaluate_suite(source, args.tests.read_text(encoding="utf-8"), timeout_seconds=args.timeout)
    print_evaluation_summary(result)
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
