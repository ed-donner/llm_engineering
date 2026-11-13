"""Local Gradio dashboard for the existing generation/evaluation pipeline."""

from html import escape
import os
from pathlib import Path
import re

from dotenv import load_dotenv
import gradio as gr
from openai import APIConnectionError, AuthenticationError, OpenAIError, RateLimitError

from benchmark import run_benchmark
from evaluate_mutants import EvaluationResult, evaluate_suite, mutants
from generate_tests import GenerationError, GenerationResult, SPEC


ROOT = Path(__file__).parent
EFFORTS = ["minimal", "low", "medium", "high", "xhigh"]
CSS = """
.gradio-container { max-width: 1200px !important; margin: auto; }
.hero { background: #14213d; color: #fff; padding: 30px; border-radius: 18px;
        margin: 12px 0 22px; }
.hero .eyebrow { color: #a5b4fc; font-size: 12px; letter-spacing: .14em; }
.hero h1 { color: #fff; font-size: clamp(26px, 4vw, 38px); margin: 8px 0; }
.hero p { color: #dbe3f5; max-width: 720px; line-height: 1.6; }
.metric-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
               gap: 12px; margin: 10px 0 16px; }
.metric { border: 1px solid var(--border-color-primary); border-radius: 12px;
          padding: 18px; background: var(--block-background-fill); }
.metric small { color: var(--body-text-color-subdued); }
.metric strong { display: block; font-size: 24px; margin: 8px 0; }
.run-note { padding: 14px 16px; border-left: 3px solid #818cf8;
            background: var(--background-fill-secondary); border-radius: 6px;
            line-height: 1.6; margin-bottom: 12px; }
.mutant-table { width: 100%; border-collapse: collapse; text-align: left; }
.mutant-table th, .mutant-table td { padding: 14px 10px;
    border-bottom: 1px solid var(--border-color-primary); }
.mutant-table th { color: var(--body-text-color-subdued); font-size: 12px;
                   text-transform: uppercase; letter-spacing: .06em; }
.badge { display: inline-block; padding: 4px 10px; border-radius: 20px;
         font-size: 12px; font-weight: 650; white-space: nowrap; }
.killed { background: #dcfce7; color: #166534; }
.survived { background: #fef3c7; color: #92400e; }
.error { background: #fee2e2; color: #991b1b; }
.not_run { background: #e2e8f0; color: #475569; }
#run-controls { padding: 20px; border-radius: 14px; }
@media (max-width: 600px) {
  .metric-grid { grid-template-columns: 1fr; }
  .hero { padding: 22px; }
  .mutant-table th, .mutant-table td { padding: 12px 4px; }
}
"""


def redact(text: str) -> str:
    """Remove the configured OpenAI key and recognizable key/bearer strings."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        text = text.replace(key, "[REDACTED]")
    text = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", text)
    return re.sub(r"(?i)bearer\s+[^\s\"']+", "Bearer [REDACTED]", text)


def summary(reference: str, score: str, source: str, note: str) -> str:
    cards = "".join(
        f'<div class="metric"><small>{label}</small><strong>{escape(value)}</strong></div>'
        for label, value in (("Correct implementation", reference),
                             ("Mutation score", score), ("Suite evaluated", source))
    )
    return f'<div class="metric-grid">{cards}</div><div class="run-note" role="status">{escape(note)}</div>'


def mutant_table(result: EvaluationResult | None = None) -> str:
    rows = [(m.name, m.status) for m in result.mutants] if result else [
        (m["name"], "not_run") for m in mutants
    ]
    body = "".join(
        f'<tr><td>{escape(name)}</td><td><span class="badge {status}">'
        f'{status.replace("_", " ").title()}</span></td></tr>'
        for name, status in rows
    )
    return '<table class="mutant-table"><thead><tr><th>Deliberate bug</th><th>Result</th></tr></thead><tbody>' + body + '</tbody></table>'


def generation_details(generation: GenerationResult | None) -> str:
    if generation is None:
        return "No fresh generation metadata. Frozen replay makes **no OpenAI request**."
    metadata = generation.metadata
    rows = [
        ("Model", metadata.model), ("Returned model", metadata.response_model),
        ("Reasoning effort", metadata.reasoning_effort),
        ("Generation time", f"{metadata.latency_seconds:.2f} seconds"),
        ("Input tokens", metadata.input_tokens), ("Output tokens", metadata.output_tokens),
        ("Reasoning tokens", metadata.reasoning_tokens), ("Total tokens", metadata.total_tokens),
        ("Response status", metadata.status),
    ]
    if metadata.incomplete_reason:
        rows.append(("Incomplete reason", metadata.incomplete_reason))
    table = "| Generation detail | Value |\n| --- | --- |\n"
    for name, value in rows:
        safe = escape(redact(str(value))) if value is not None else "Not reported"
        safe = safe.replace("|", "&#124;").replace("\n", " ")
        table += f"| {name} | {safe} |\n"
    return table + "\nReasoning tokens are included in output tokens, not added again."


def render_result(result: EvaluationResult, generation: GenerationResult | None = None):
    """Adapt existing result objects into the five dashboard outputs."""
    reference = "Passed" if result.reference_passed else "Did not pass"
    if result.mutation_score is None:
        score = "Unavailable"
        note = (
            "The suite did not pass on the correct implementation. Mutants were not run; "
            "no valid mutation score can be reported. Open the pytest logs for details."
            if not result.reference_passed else
            "The correct implementation passed, but at least one mutant evaluation errored. "
            "Errors do not count as kills, so the mutation score is unavailable. See the pytest logs."
        )
    else:
        score = f"{result.mutants_killed}/{result.total_mutants} · {result.mutation_score:.0f}%"
        note = (
            f"Evaluation complete. {result.reference.passed} tests passed on the correct implementation. "
            "Killed means the tests detected a deliberate bug; survived means they missed it."
        )
    runs = [("Correct implementation", result.reference, result.reference.error)]
    runs.extend((m.name, m.pytest, m.error) for m in result.mutants)
    logs = []
    for name, run, error in runs:
        detail = f"=== {name} ===\n"
        if run is not None:
            detail += f"Status: {run.status}; exit code: {run.returncode}; time: {run.latency_seconds:.2f}s\n"
            detail += f"Passed: {run.passed}; failed: {run.failed}; errors: {run.errors}; skipped: {run.skipped}\n"
            detail += (error or "") + "\n" + run.stdout + "\n" + run.stderr
        else:
            detail += error or "Not run."
        logs.append(detail)
    return (
        summary(reference, score, "Fresh generation" if generation else "Frozen replay", note),
        mutant_table(result), redact(generation.test_code) if generation else "",
        generation_details(generation), redact("\n\n".join(logs)),
    )


def error_view(message: str, generation: GenerationResult | None = None):
    return (
        summary("Not evaluated", "Unavailable", "No evaluation", message),
        mutant_table(), redact(generation.test_code) if generation else "",
        generation_details(generation) if generation else "No generation metadata available.",
        "Evaluation was not completed. " + message,
    )


def replay_frozen():
    """Free path: never load credentials or call the generation function."""
    try:
        source = (ROOT / "solution.py").read_text(encoding="utf-8")
        tests = (ROOT / "test_generated.py").read_text(encoding="utf-8")
        return render_result(evaluate_suite(source, tests))
    except Exception:
        # Raw exceptions can include credentials or sensitive local paths.
        return error_view("Frozen replay could not complete. Check that the project files and pytest environment are available.")


def generate_and_evaluate(model: str, reasoning_effort: str):
    """Paid path: delegate generation and evaluation to run_benchmark."""
    if not model.strip() or reasoning_effort not in EFFORTS:
        return error_view("Enter a model name and select a reasoning effort before generating.")
    try:
        load_dotenv(ROOT / ".env")
        if not os.getenv("OPENAI_API_KEY", "").strip():
            return error_view("OpenAI API key missing. Set OPENAI_API_KEY in the project .env or terminal environment, then retry. Frozen replay is still free.")
        source = (ROOT / "solution.py").read_text(encoding="utf-8")
        result = run_benchmark(SPEC, source, model.strip(), reasoning_effort)
        return render_result(result.evaluation, result.generation)
    except GenerationError as exc:
        return error_view(
            "Generation returned incomplete or empty output. Evaluation was skipped. "
            "Any code below is partial output; generation details show the response status.",
            exc.result,
        )
    except AuthenticationError:
        return error_view("OpenAI could not authenticate. Check the API key configured on this computer. Do not paste it into the model field.")
    except RateLimitError:
        return error_view("OpenAI could not accept the request because of a rate or credit limit. Check your account and retry later.")
    except APIConnectionError:
        return error_view("Could not connect to OpenAI. Check your internet connection and retry.")
    except OpenAIError:
        return error_view("OpenAI rejected or failed the request. Check model access, reasoning-effort support, and account configuration.")
    except Exception:
        return error_view("Generation or evaluation could not complete. Check the project files and Python environment. No valid score was recorded.")


def build_app() -> gr.Blocks:
    with gr.Blocks(title="LLM Test Lab", analytics_enabled=False) as demo:
        gr.HTML('''<header class="hero">
            <div class="eyebrow">WEEK 04 / AI ENGINEERING · LOCAL WORKSPACE</div>
            <h1>Put your tests to the test.</h1>
            <p>Generate Python tests with an LLM, then check whether they catch five
            deliberate bugs in <code>shipping_fee()</code>. Start with a free replay.</p>
            </header>''')
        with gr.Row():
            with gr.Column(scale=1, min_width=300, variant="panel", elem_id="run-controls"):
                gr.Markdown("### Start with the saved suite\nRun the frozen 20 tests. No API key or credits needed.")
                replay = gr.Button("Replay Frozen Tests (Free)", variant="secondary")
                gr.Markdown("---\n### Generate a fresh suite\nThese settings apply only to fresh generation.")
                model = gr.Textbox(value="gpt-6-luna", label="OpenAI model", max_length=120)
                effort = gr.Dropdown(EFFORTS, value="low", label="Reasoning effort",
                                     info="Supported settings depend on the selected model.")
                generate = gr.Button("Generate & Evaluate (Uses API Credits)", variant="primary")
                gr.Markdown("Uses your locally configured OpenAI key. New tests do not overwrite the frozen suite.")
                with gr.Accordion("What is being tested?", open=False):
                    gr.Markdown(SPEC)
            with gr.Column(scale=2, min_width=300):
                gr.Markdown("### Evaluation overview")
                overview = gr.HTML(summary("Not run", "—", "None yet", "Choose free replay or generate a new suite to begin."))
                table = gr.HTML(mutant_table())
                with gr.Tab("Generated Python"):
                    gr.Markdown("Freshly generated code appears here. Frozen replay uses the saved suite without generating new code.")
                    code = gr.Code(language="python", label="Generated pytest code", interactive=False,
                                   lines=10, max_lines=24, wrap_lines=True)
                with gr.Tab("Generation details"):
                    metadata = gr.Markdown("Generation metadata will appear after an API run.")
                with gr.Accordion("Detailed pytest logs", open=False):
                    logs = gr.Textbox(label="Run diagnostics", interactive=False, lines=12, max_lines=24)
        gr.Markdown("**Local use only.** Generated Python executes on this computer. Temporary directories are not secure sandboxes; do not expose this app publicly.")
        outputs = [overview, table, code, metadata, logs]
        for button, callback, inputs in (
            (replay, replay_frozen, []),
            (generate, generate_and_evaluate, [model, effort]),
        ):
            button.click(
                fn=callback, inputs=inputs, outputs=outputs,
                api_visibility="private", concurrency_id="evaluation", concurrency_limit=1,
                trigger_mode="once", show_progress="full", show_progress_on=overview,
            )
    return demo.queue(default_concurrency_limit=1, max_size=4)


def main() -> None:
    build_app().launch(
        server_name="127.0.0.1", share=False, show_error=False,
        theme=gr.themes.Soft(primary_hue="indigo", neutral_hue="slate",
                             font=["system-ui", "sans-serif"], font_mono=["monospace"]),
        css=CSS, footer_links=[], enable_monitoring=False, mcp_server=False,
        ssr_mode=False, blocked_paths=[str(ROOT / ".env"), str(ROOT / ".git")],
    )


if __name__ == "__main__":
    main()
