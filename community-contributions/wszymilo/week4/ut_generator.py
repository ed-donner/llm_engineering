"""
AI Unit Tests Generator: paste Python code, generate and run pytest unit tests via Gradio.
"""

import os
import subprocess
import sys
import tempfile

from dotenv import find_dotenv, load_dotenv
import gradio as gr
from openai import OpenAI

# -----------------------------------------------------------------------------
# Config and clients
# -----------------------------------------------------------------------------

load_dotenv(find_dotenv(), override=True)
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

if openai_api_key:
    print(f"OpenAI API key present (starts with {openai_api_key[:8]}...)")
else:
    print("OpenAI API key not set")
if anthropic_api_key:
    print(f"Anthropic API key present (starts with {anthropic_api_key[:7]}...)")
else:
    print("Anthropic API key not set")

openai_client = OpenAI()
anthropic_client = OpenAI(
    api_key=anthropic_api_key or "",
    base_url="https://api.anthropic.com/v1/",
)

MODELS = [
    "gpt-4o-mini",
    "gpt-5-nano",
    "claude-haiku-4-5",
    "claude-3-haiku-20240307"
]

CLIENTS = {
    "gpt-4o-mini": openai_client,
    "gpt-5-nano": openai_client,
    "claude-haiku-4-5": anthropic_client,
    "claude-3-haiku-20240307": anthropic_client,
}

# -----------------------------------------------------------------------------
# Prompts (pytest only)
# -----------------------------------------------------------------------------

SYSTEM_PROMPT = """You generate Python unit tests using pytest only.
The tool will automatically prepend the user's source code above your output when running tests, so output ONLY the test code. Do not copy or repeat the code under test.

Requirements:
- Use `import pytest`.
- Define test functions named `test_*` that reference the names (functions, classes) defined in the user's code (they will be in the same file at run time).
- Use pytest-style assertions (e.g. assert x == y).
- End the script with: if __name__ == "__main__": pytest.main(["-v"])
Respond only with runnable pytest code. No explanation, no markdown, no code fences."""


def user_prompt_for(python_code: str) -> str:
    return f"""Generate pytest unit tests for the following Python code.
Output ONLY the test code (no copy of the code below). The tool will run the code below first, then your tests in the same file.
Use test_* functions and end with: if __name__ == "__main__": pytest.main(["-v"])
Respond only with the test code, no markdown or explanation.

```python
{python_code}
```"""


def messages_for(python_code: str):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt_for(python_code)},
    ]


def strip_code_fences(text: str) -> str:
    """Remove optional markdown code fences from start/end of string."""
    s = text.strip()
    if s.startswith("```python"):
        s = s[len("```python") :].lstrip("\n")
    elif s.startswith("```"):
        s = s[3:].lstrip("\n")
    if s.rstrip().endswith("```"):
        s = s[: s.rstrip().rfind("```")].rstrip()
    return s


# -----------------------------------------------------------------------------
# Core logic
# -----------------------------------------------------------------------------


def generate_tests(model: str, python_code: str, progress=gr.Progress()):
    """Stream generated pytest code into the UI. Yields accumulated content."""
    if progress is not None:
        progress(0, desc="Connecting...")
    client = CLIENTS.get(model)
    if not client:
        yield "Error: unknown model"
        return
    if progress is not None:
        progress(0.2, desc="Generating tests...")
    accumulated = ""
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages_for(python_code),
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                accumulated += chunk.choices[0].delta.content
                cleaned = strip_code_fences(accumulated)
                yield cleaned
    except Exception as e:
        accumulated += f"\n\nError: {e}"
        yield strip_code_fences(accumulated)
    if progress is not None:
        progress(1, desc="Done")


def run_tests(source_code: str, test_code: str, progress=gr.Progress()):
    """Run pytest in a subprocess on a temp file containing source + test code; return stdout/stderr."""
    if progress is not None:
        progress(0, desc="Preparing test file ...")
    with tempfile.TemporaryDirectory(prefix="pytest_run_") as tmpdir:
        combined = source_code.strip() + "\n\n" + test_code.strip()
        filepath = os.path.join(tmpdir, "test_run.py")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(combined)

        if progress is not None:
            progress(0.2, desc="Running tests ...")

        result_proc = subprocess.run(
            [sys.executable, "-m", "pytest", filepath, "-v"],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            timeout=60,
            check=False
        )
        if progress is not None:
            progress(0.8, desc="Tests completed")

        out = result_proc.stdout or ""
        err = result_proc.stderr or ""
        result = out.strip()
        if err.strip():
            result += "\n\n" + err.strip()
    if progress is not None:
        progress(1, desc="Done")
    return result or "(no output)"


# -----------------------------------------------------------------------------
# Gradio UI
# -----------------------------------------------------------------------------

DEFAULT_PLACEHOLDER = """# Paste your Python code here
def add(a, b):
    return a + b
"""


# Fixed-width font for test output
OUTPUT_CSS = """
.test-output-mono textarea {
    font-family: ui-monospace, "Cascadia Code", "Source Code Pro", Menlo, Consolas, "DejaVu Sans Mono", monospace !important;
    font-size: 13px;
}
"""


def build_ui():
    with gr.Blocks(
        css=OUTPUT_CSS,
        theme=gr.themes.Monochrome(),
        title="AI Unit Tests Generator",
    ) as ui:
        with gr.Row(equal_height=True):
            python_code = gr.Code(
                label="Python code",
                value=DEFAULT_PLACEHOLDER,
                language="python",
                lines=20,
            )
            tests_code = gr.Code(
                label="Generated unit tests",
                value="",
                language="python",
                lines=20,
            )
        with gr.Row(elem_classes=["controls"]):
            model_dropdown = gr.Dropdown(
                MODELS, value=MODELS[0], label="Model", container=False
            )
            gen_btn = gr.Button("Generate tests", elem_classes=["convert-btn"])
        with gr.Row():
            run_btn = gr.Button("Run tests", elem_classes=["run-btn"])
        with gr.Row():
            test_output = gr.TextArea(
                label="Test run output",
                lines=12,
                elem_classes=["test-output-mono"],
            )

        gen_btn.click(
            fn=generate_tests,
            inputs=[model_dropdown, python_code],
            outputs=[tests_code],
        )
        run_btn.click(
            fn=run_tests,
            inputs=[python_code, tests_code],
            outputs=[test_output],
        )
    return ui


if __name__ == "__main__":
    ui = build_ui()
    ui.queue().launch(inbrowser=False, server_name="0.0.0.0")
