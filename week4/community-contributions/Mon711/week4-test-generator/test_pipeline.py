"""Offline checks for generation wiring, isolation and honest scoring."""

from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import benchmark
import evaluate_mutants as evaluator
import generate_tests as generator


ROOT = Path(__file__).parent
SOURCE = (ROOT / "solution.py").read_text(encoding="utf-8")
FROZEN_SUITE = (ROOT / "test_generated.py").read_text(encoding="utf-8")


@pytest.fixture
def fake_client():
    response = SimpleNamespace(
        output_text=FROZEN_SUITE, id="response-test", model="gpt-6-luna",
        status="completed", incomplete_details=None,
        usage=SimpleNamespace(
            input_tokens=100, output_tokens=200, total_tokens=300,
            output_tokens_details=SimpleNamespace(reasoning_tokens=50),
        ),
    )
    client = Mock()
    client.responses.create.return_value = response
    return client


def test_generation_parameters_prompt_and_metadata(fake_client, monkeypatch):
    clock = iter([10.0, 12.5])
    monkeypatch.setattr(generator, "perf_counter", lambda: next(clock))
    result = generator.generate_tests(
        "example requirements", "example source", "gpt-6-luna", "medium",
        client=fake_client,
    )
    request = fake_client.responses.create.call_args.kwargs
    assert request["model"] == "gpt-6-luna"
    assert request["reasoning"] == {"effort": "medium"}
    assert request["max_output_tokens"] == 2500
    # Exact original wording and whitespace, rather than a redesigned prompt.
    assert request["instructions"] == """
You are an expert Python testing engineer.

Generate a pytest test suite for the provided Python function.

The tests must:
- test the documented behaviour thoroughly,
- include important boundary and edge cases,
- import shipping_fee from solution,
- contain only valid Python pytest code.

Return only the Python code. Do not use Markdown code fences.
"""
    assert request["input"] == "\nREQUIREMENTS:\n\nexample requirements\n\nIMPLEMENTATION:\n\nexample source\n\n"
    assert result.test_code == FROZEN_SUITE
    assert asdict(result.metadata) == {
        "model": "gpt-6-luna", "reasoning_effort": "medium",
        "latency_seconds": 2.5, "input_tokens": 100, "output_tokens": 200,
        "reasoning_tokens": 50, "total_tokens": 300,
        "response_id": "response-test", "response_model": "gpt-6-luna",
        "status": "completed", "incomplete_reason": None,
    }


@pytest.mark.parametrize("usage", [None, SimpleNamespace(input_tokens=4, output_tokens=8, total_tokens=12)])
def test_missing_usage_is_unknown_not_zero(fake_client, usage):
    fake_client.responses.create.return_value.usage = usage
    result = generator.generate_tests(generator.SPEC, SOURCE, client=fake_client)
    assert result.metadata.reasoning_tokens is None
    assert result.metadata.total_tokens == (None if usage is None else 12)


@pytest.mark.parametrize("status, code", [("incomplete", "def test_partial():"), ("completed", "")])
def test_incomplete_or_empty_generation_keeps_metadata(fake_client, status, code):
    response = fake_client.responses.create.return_value
    response.status, response.output_text = status, code
    response.incomplete_details = SimpleNamespace(reason="max_output_tokens")
    with pytest.raises(generator.GenerationError) as error:
        generator.generate_tests(generator.SPEC, SOURCE, client=fake_client)
    assert error.value.result.test_code == code
    assert error.value.result.metadata.total_tokens == 300


def test_frozen_suite_regression_and_file_isolation(monkeypatch):
    before = {name: (ROOT / name).read_bytes() for name in ("solution.py", "test_generated.py")}
    # These inherited settings must not alter subprocess evaluation.
    monkeypatch.setenv("PYTEST_ADDOPTS", "--invalid-option")
    monkeypatch.setenv("PYTEST_PLUGINS", "missing_plugin")
    result = evaluator.evaluate_suite(SOURCE, FROZEN_SUITE)
    assert result.status == "completed"
    assert result.reference_passed
    assert result.reference.passed == 20
    assert result.mutants_killed == result.total_mutants == 5
    assert result.mutation_score == 100
    assert all(m.status == "killed" for m in result.mutants)
    assert {name: (ROOT / name).read_bytes() for name in before} == before


@pytest.mark.parametrize("suite, reference_status", [
    ("def test_wrong():\n    assert False\n", "failed"),
    ("def test_broken(:\n", "error"),
    ("import nonexistent_shipping_dependency\n", "error"),
    ("# No tests\n", "error"),
    ("import pytest\n@pytest.mark.skip\ndef test_skip():\n    pass\n", "error"),
    ("def test_runtime():\n    raise RuntimeError('broken test')\n", "error"),
    ("import pytest\n@pytest.fixture\ndef broken():\n    raise RuntimeError('broken fixture')\ndef test_fixture(broken):\n    pass\n", "error"),
    ("import pytest\n@pytest.fixture\ndef broken():\n    yield\n    raise RuntimeError('broken teardown')\ndef test_fixture(broken):\n    pass\n", "error"),
])
def test_invalid_reference_stops_before_mutants(suite, reference_status, monkeypatch):
    runner = Mock(wraps=evaluator.run_pytest)
    monkeypatch.setattr(evaluator, "run_pytest", runner)
    result = evaluator.evaluate_suite(SOURCE, suite)
    assert runner.call_count == 1
    assert result.status == "invalid"
    assert result.reference.status == reference_status
    assert not result.reference_passed
    assert result.mutation_score is None
    assert result.mutants_killed == 0
    assert len(result.mutants) == 5
    assert all(m.status == "not_run" for m in result.mutants)
    if reference_status == "error":
        assert result.reference.error


def test_legitimate_survivors_have_zero_score():
    suite = """
import pytest
from solution import shipping_fee
def test_negative():
    with pytest.raises(ValueError):
        shipping_fee(-1, False, False)
"""
    result = evaluator.evaluate_suite(SOURCE, suite)
    assert result.status == "completed"
    assert result.reference_passed
    assert result.mutation_score == 0
    assert all(m.status == "survived" for m in result.mutants)


@pytest.mark.parametrize("failure_location", ["fixture", "test"])
def test_mutant_runtime_error_is_not_a_kill(failure_location):
    # Reference passes; express-cost mutant triggers a test/fixture bug.
    check = "if shipping_fee(1000, False, True) == 100:\n        raise RuntimeError('test infrastructure broke')"
    suite = "import pytest\nfrom solution import shipping_fee\n"
    if failure_location == "fixture":
        suite += f"@pytest.fixture\ndef check():\n    {check}\ndef test_fee(check):\n    assert shipping_fee(1000, False, False) == 0\n"
    else:
        suite += f"def test_fee():\n    {check}\n    assert shipping_fee(1000, False, False) == 0\n"
    result = evaluator.evaluate_suite(SOURCE, suite)
    assert result.reference_passed
    assert result.status == "error"
    assert result.mutation_score is None
    assert result.mutants_killed == 1  # Only the threshold mutant fails an assertion.
    express = result.mutants[2]
    assert express.status == "error"
    assert express.pytest.errors == 1
    assert "RuntimeError" in express.pytest.stdout


def test_missing_mutation_target_is_an_error():
    source = SOURCE.replace("else 80", "else (80)")  # Same behavior, different text.
    result = evaluator.evaluate_suite(source, FROZEN_SUITE)
    assert result.reference_passed
    assert result.mutants[-1].status == "error"
    assert result.mutants[-1].pytest is None
    assert result.mutation_score is None


def test_timeout_returns_error_and_cleans_up(monkeypatch):
    directories = []
    original_run = subprocess.run

    def record_directory(*args, **kwargs):
        directories.append(Path(kwargs["cwd"]))
        return original_run(*args, **kwargs)

    monkeypatch.setattr(evaluator.subprocess, "run", record_directory)
    result = evaluator.run_pytest(
        SOURCE, "import time\ndef test_slow():\n    time.sleep(60)\n",
        timeout_seconds=1,
    )
    assert result.status == "error"
    assert result.returncode is None
    assert "timed out" in result.error
    assert directories and not directories[0].exists()


def test_subprocess_launch_error_is_reported(monkeypatch):
    def cannot_launch(*args, **kwargs):
        raise OSError("cannot launch Python")

    monkeypatch.setattr(evaluator.subprocess, "run", cannot_launch)
    result = evaluator.run_pytest(SOURCE, FROZEN_SUITE)
    assert result.status == "error"
    assert "cannot launch Python" in result.error


def test_missing_report_is_not_a_kill(monkeypatch):
    monkeypatch.setattr(evaluator.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 1, "unexpected failure", ""))
    result = evaluator.run_pytest(SOURCE, FROZEN_SUITE)
    assert result.status == "error"
    assert "pytest report" in result.error
    assert result.stdout == "unexpected failure"


def test_malformed_report_returns_error(monkeypatch):
    def malformed_report(*args, **kwargs):
        (Path(kwargs["cwd"]) / "pytest_results.json").write_text(
            '["passed", "failed", "errors", "skipped", "collected"]',
        )
        return subprocess.CompletedProcess(args[0], 1, "", "")

    monkeypatch.setattr(evaluator.subprocess, "run", malformed_report)
    result = evaluator.run_pytest(SOURCE, FROZEN_SUITE)
    assert result.status == "error"
    assert "invalid pytest report" in result.error


def test_early_exit_zero_is_not_a_pass():
    suite = """
import pytest
def test_first():
    assert True
def test_abort():
    pytest.exit('stopped early', returncode=0)
"""
    result = evaluator.run_pytest(SOURCE, suite)
    assert result.returncode == 0
    assert result.status == "error"
    assert "before every collected test" in result.error


def test_uses_active_interpreter_and_fresh_directories(monkeypatch):
    directories = []
    original_run = subprocess.run

    def inspect_run(command, **kwargs):
        assert command[:3] == [sys.executable, "-m", "pytest"]
        directory = Path(kwargs["cwd"])
        assert directory != ROOT
        assert (directory / "solution.py").exists()
        assert (directory / "test_generated.py").exists()
        directories.append(directory)
        return original_run(command, **kwargs)

    monkeypatch.setattr(evaluator.subprocess, "run", inspect_run)
    assert evaluator.evaluate_suite(SOURCE, FROZEN_SUITE).status == "completed"
    assert len(directories) == len(set(directories)) == 6
    assert all(not directory.exists() for directory in directories)


def test_end_to_end_generation_and_real_pytest(fake_client):
    result = benchmark.run_benchmark(generator.SPEC, SOURCE, client=fake_client)
    assert fake_client.responses.create.call_count == 1
    assert result.generation.metadata.total_tokens == 300
    assert result.evaluation.reference.passed == 20
    assert result.evaluation.mutation_score == 100


def test_imports_have_no_api_or_file_side_effects(tmp_path):
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    env["PYTHONPATH"] = str(ROOT)
    completed = subprocess.run(
        [sys.executable, "-c", "import generate_tests, evaluate_mutants, benchmark"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert not list(tmp_path.iterdir())


def test_cli_replay_json_and_exit_status(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(sys, "argv", ["benchmark.py", "--tests", str(ROOT / "test_generated.py"), "--json"])
    assert benchmark.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["generation"] is None
    assert report["evaluation"]["mutation_score"] == 100
    invalid = tmp_path / "invalid.py"
    invalid.write_text("def test_wrong():\n    assert False\n")
    monkeypatch.setattr(sys, "argv", ["benchmark.py", "--tests", str(invalid)])
    assert benchmark.main() == 1
    assert "unavailable (invalid)" in capsys.readouterr().out


def test_invalid_timeout_does_not_call_openai(fake_client):
    with pytest.raises(ValueError, match="positive"):
        benchmark.run_benchmark(generator.SPEC, SOURCE, client=fake_client, timeout_seconds=0)
    fake_client.responses.create.assert_not_called()
