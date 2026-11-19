"""Focused dashboard checks; generation is mocked and never spends credits."""

import asyncio
from dataclasses import replace
from unittest.mock import Mock

import gradio as gr
import pytest
from openai import OpenAIError

import app
from benchmark import BenchmarkResult
from evaluate_mutants import EvaluationResult, MutantResult, PytestResult
from generate_tests import GenerationError, GenerationMetadata, GenerationResult


@pytest.fixture
def completed():
    reference = PytestResult("passed", 0, 0.1, stdout="20 passed", passed=20, collected=20)
    failed = PytestResult("failed", 1, 0.1, stdout="AssertionError: deliberate bug", failed=1, collected=1)
    return EvaluationResult(
        "completed", True, reference, 5, 5, 100.0,
        [MutantResult(m["name"], "killed", failed) for m in app.mutants],
    )


@pytest.fixture
def generation():
    return GenerationResult(
        "def test_example():\n    assert True\n",
        GenerationMetadata(
            model="gpt-6-luna", reasoning_effort="low", latency_seconds=1.25,
            input_tokens=100, output_tokens=200, reasoning_tokens=50, total_tokens=300,
            response_id="test", response_model="gpt-6-luna", status="completed", incomplete_reason=None,
        ),
    )


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "local-test-secret")
    monkeypatch.setattr(app, "load_dotenv", Mock())


def test_frozen_callback_uses_real_evaluator_without_generation(monkeypatch):
    api = Mock(side_effect=AssertionError("must not generate"))
    credentials = Mock(side_effect=AssertionError("must not load credentials"))
    monkeypatch.setattr(app, "run_benchmark", api)
    monkeypatch.setattr(app, "load_dotenv", credentials)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    before = [(app.ROOT / name).read_bytes() for name in ("solution.py", "test_generated.py")]
    overview, table, code, metadata, logs = app.replay_frozen()
    assert "Passed" in overview and "5/5 · 100%" in overview
    assert table.count(">Killed</span>") == 5
    assert code == ""  # Clear code from any previous generation.
    assert "no OpenAI request" in metadata
    assert "20 passed" in logs
    assert before == [(app.ROOT / name).read_bytes() for name in ("solution.py", "test_generated.py")]
    api.assert_not_called()
    credentials.assert_not_called()


def test_generation_callback_reuses_benchmark_and_displays_metadata(monkeypatch, configured, completed, generation):
    run = Mock(return_value=BenchmarkResult(generation, completed))
    monkeypatch.setattr(app, "run_benchmark", run)
    overview, table, code, metadata, logs = app.generate_and_evaluate(" gpt-6-luna ", "low")
    run.assert_called_once_with(app.SPEC, (app.ROOT / "solution.py").read_text(), "gpt-6-luna", "low")
    assert "Fresh generation" in overview
    assert code == generation.test_code
    assert "1.25 seconds" in metadata and "300" in metadata and "50" in metadata
    assert "gpt-6-luna" in metadata


def test_missing_key_never_calls_benchmark(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(app, "load_dotenv", Mock())
    run = Mock()
    monkeypatch.setattr(app, "run_benchmark", run)
    output = app.generate_and_evaluate("gpt-6-luna", "low")
    assert "API key missing" in output[0]
    assert "Unavailable" in output[0] and output[2] == ""
    run.assert_not_called()


def test_incomplete_generation_keeps_partial_code_without_evaluating(monkeypatch, configured, generation):
    partial = replace(generation, metadata=replace(generation.metadata, status="incomplete", incomplete_reason="max_output_tokens"))
    run = Mock(side_effect=GenerationError("private upstream diagnostic", partial))
    monkeypatch.setattr(app, "run_benchmark", run)
    output = app.generate_and_evaluate("gpt-6-luna", "low")
    assert "Evaluation was skipped" in output[0]
    assert output[2] == partial.test_code and "incomplete" in output[3]
    assert output[1].count(">Not Run</span>") == 5
    assert "private upstream diagnostic" not in str(output)


@pytest.mark.parametrize("error", [OpenAIError("local-test-secret sk-remote-secret"), RuntimeError("local-test-secret /private/file")])
def test_upstream_errors_do_not_expose_exception_text(monkeypatch, configured, error):
    monkeypatch.setattr(app, "run_benchmark", Mock(side_effect=error))
    output = app.generate_and_evaluate("gpt-6-luna", "low")
    assert "Unavailable" in output[0] and output[2] == ""
    assert "local-test-secret" not in str(output)
    assert "sk-remote-secret" not in str(output)
    assert "/private/file" not in str(output)


@pytest.mark.parametrize("model, effort", [(" ", "low"), ("gpt-6-luna", "invalid")])
def test_invalid_settings_do_not_start_generation(monkeypatch, model, effort):
    run = Mock()
    monkeypatch.setattr(app, "run_benchmark", run)
    assert "Enter a model name" in app.generate_and_evaluate(model, effort)[0]
    run.assert_not_called()


def test_invalid_reference_and_mutant_errors_explain_missing_score(completed):
    invalid = replace(completed, status="invalid", reference_passed=False, mutation_score=None)
    output = app.render_result(invalid)
    assert "suite did not pass" in output[0] and "Unavailable" in output[0]
    error = PytestResult("error", 2, 0.1, stderr="collection problem", error="could not collect")
    bad_mutant = replace(completed.mutants[0], status="error", pytest=error, error=error.error)
    broken = replace(completed, status="error", mutation_score=None, mutants=[bad_mutant, *completed.mutants[1:]])
    output = app.render_result(broken)
    assert "at least one mutant evaluation errored" in output[0]
    assert ">Error</span>" in output[1]
    assert "collection problem" in output[4]


def test_survivors_and_zero_score_remain_valid(completed):
    survivors = [replace(m, status="survived") for m in completed.mutants]
    output = app.render_result(replace(completed, mutants_killed=0, mutation_score=0, mutants=survivors))
    assert "0/5 · 0%" in output[0]
    assert output[1].count(">Survived</span>") == 5
    assert "Unavailable" not in output[0]


def test_log_code_and_metadata_redaction(configured, completed, generation):
    secret = "local-test-secret"
    reference = replace(completed.reference, stdout=f"{secret} sk-another-secret Bearer credential")
    generation = replace(generation, test_code=f"# {secret}", metadata=replace(generation.metadata, model=f"<script>{secret}</script>"))
    output = app.render_result(replace(completed, reference=reference), generation)
    assert secret not in str(output) and "sk-another-secret" not in str(output)
    assert "Bearer credential" not in str(output)
    assert "<script>" not in output[3] and "&lt;script&gt;" in output[3]


def test_blocks_events_connect_the_correct_inputs_and_all_outputs(monkeypatch, completed, generation):
    # Exercise actual Gradio preprocessing/postprocessing, without a server or API call.
    replay = Mock(return_value=app.render_result(completed))
    generate = Mock(return_value=app.render_result(completed, generation))
    replay.__name__, generate.__name__ = "replay_frozen", "generate_and_evaluate"
    monkeypatch.setattr(app, "replay_frozen", replay)
    monkeypatch.setattr(app, "generate_and_evaluate", generate)
    demo = app.build_app()
    handlers = list(demo.fns.values())
    assert len(handlers) == 2
    assert len(handlers[0].inputs) == 0 and len(handlers[1].inputs) == 2
    assert [component.value for component in handlers[1].inputs] == ["gpt-6-luna", "low"]
    assert handlers[0].outputs == handlers[1].outputs
    assert [type(c) for c in handlers[0].outputs] == [gr.HTML, gr.HTML, gr.Code, gr.Markdown, gr.Textbox]
    assert all(h.api_visibility == "private" and h.concurrency_limit == 1 for h in handlers)
    assert handlers[0].concurrency_id == handlers[1].concurrency_id == "evaluation"
    replay_output = asyncio.run(demo.process_api(handlers[0], []))
    generate_output = asyncio.run(demo.process_api(handlers[1], ["gpt-6-luna", "low"]))
    assert len(replay_output["data"]) == len(generate_output["data"]) == 5
    replay.assert_called_once_with()
    generate.assert_called_once_with("gpt-6-luna", "low")


def test_main_uses_gradio6_launch_settings_and_loopback_only(monkeypatch):
    demo = Mock()
    monkeypatch.setattr(app, "build_app", Mock(return_value=demo))
    app.main()
    settings = demo.launch.call_args.kwargs
    assert settings["server_name"] == "127.0.0.1"
    assert settings["share"] is False and settings["show_error"] is False
    assert settings["mcp_server"] is False and settings["enable_monitoring"] is False
    assert settings["css"] == app.CSS and isinstance(settings["theme"], gr.themes.Soft)
