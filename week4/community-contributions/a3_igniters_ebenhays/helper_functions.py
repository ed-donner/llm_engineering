import os
import time
import subprocess
import tempfile
import re
import builtins as _builtins

from dotenv import load_dotenv
from openai import OpenAI

namespace = {"__builtins__": _builtins}

# Load environment variables and initialize OpenAI client
load_dotenv(override=True)
openrouter_url = "https://openrouter.ai/api/v1"
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
if not openrouter_api_key:
    raise ValueError("OPENROUTER_API_KEY is not set")
openrouter = OpenAI(base_url=openrouter_url, api_key=openrouter_api_key)
print("API key loaded")


# Prompt builder
def create_solution_prompt(problem_description):
    return f"""
    You are a senior Python engineer. Solve this problem:

    {problem_description}

    Provide a clean, well-structured Python solution."""


# Code generation


def extract_code_block(text):
    """Extract code from a fenced block anywhere in the response, or return raw text."""
    match = re.search(r"```(?:python)?\n(.*?)```", text, flags=re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def generate_code(model_slug, coding_question):
    try:
        response = openrouter.chat.completions.create(
            model=model_slug,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Python engineer. Respond with ONLY a Python code block. "
                        "No explanation before or after. Start directly with ```python."
                    ),
                },
                {"role": "user", "content": create_solution_prompt(coding_question)},
            ],
        )
        return extract_code_block(response.choices[0].message.content.strip())
    except Exception as e:
        return f"# Generation failed: {type(e).__name__}: {str(e)}"


# Solution evaluation
def get_pylint_score(code):
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            filepath = f.name

        result = subprocess.run(
            ["pylint", "--score=y", "--reports=n", "--output-format=text", filepath],
            capture_output=True,
            text=True,
            timeout=10,
        )
        os.unlink(filepath)

        match = re.search(r"Your code has been rated at ([0-9.]+)/10", result.stdout)
        return float(match.group(1)) if match else 0.0
    except Exception:
        return 0.0


def evaluate_solution(code, tests):

    runtime_ms = float("inf")
    try:
        start = time.perf_counter()
        exec(code, namespace)
        runtime_ms = (time.perf_counter() - start) * 1000
    except Exception as e:
        return 0.0, float("inf"), 0.0, f"Solution exec failed: {e}"

    fns = [v for v in namespace.values() if callable(v)]
    if not fns:
        return 0.0, runtime_ms, 0.0, "No callable function found in solution"
    fn = fns[-1]

    pass_count, error = 0, None
    for test_fn in tests:
        try:
            test_fn(fn)
            pass_count += 1
        except Exception as e:
            if error is None:
                error = str(e)

    pass_pct = (pass_count / len(tests)) * 100 if tests else 0.0
    return pass_pct, runtime_ms, get_pylint_score(code), error


# Unit-test generation

TEST_FOCUSES = {
    "edge": (
        "Focus exclusively on EDGE CASES and BOUNDARY CONDITIONS:\n"
        "- Zero, negative numbers, empty inputs, None where applicable\n"
        "- Minimum and maximum boundary values\n"
        "- Single-element or single-character inputs\n"
        "- Inputs that might cause off-by-one errors"
    ),
    "typical": (
        "Focus on TYPICAL USE CASES and CORRECTNESS BREADTH:\n"
        "- Common real-world inputs a user would pass\n"
        "- A range of normal positive values\n"
        "- Verify output types and structure, not just values\n"
        "- Two or more distinct input categories to ensure general correctness"
    ),
}


def generate_unit_tests(
    problem_description,
    solution_code,
    model_slug,
    focus="typical",
):
    focus_instruction = TEST_FOCUSES.get(focus, TEST_FOCUSES["typical"])

    prompt = f"""You are a Python testing expert.

Problem: {problem_description}

Solution code to test:
```python
{solution_code}
```

Write exactly 5 test functions named test_1 through test_5.

Testing focus — your tests MUST reflect this angle:
{focus_instruction}

Rules (follow exactly):
- Each signature: def test_N(fn):
- `fn` is already the callable — call it directly, e.g. fn(5)
- Do NOT use exec(), import, or define helper functions
- Use assert with a descriptive f-string error message
- Every test must use a DIFFERENT input from the others

Example:
def test_1(fn):
    result = fn(5)
    assert result == <expected>, f"Expected <expected>, got {{result}}"

Return ONLY the 5 def blocks. No markdown fences, no imports, no commentary."""

    try:
        response = openrouter.chat.completions.create(
            model=model_slug,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Python testing expert. Respond with ONLY Python function definitions. "
                        "No explanation, no markdown preamble, no imports."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        return extract_code_block(response.choices[0].message.content.strip())
    except Exception as e:
        return f"# Test generation failed: {type(e).__name__}: {str(e)}"


def parse_tests(test_code):
    try:
        exec(test_code, namespace)
        tests = [
            v for k, v in namespace.items() if k.startswith("test_") and callable(v)
        ]
        return tests, test_code
    except Exception as exc:
        return [], f"# Failed to compile tests: {exc}"


# UI display helpers
def display_metrics(r):
    rt = f"{r['runtime_ms']:.1f} ms" if r["runtime_ms"] != float("inf") else "N/A"
    err_line = f"\n\n> ⚠️ **Error:** `{r['error']}`" if r.get("error") else ""
    return (
        f"**✅ Tests passed:** {r['pass_pct']:.1f}%  &nbsp;|&nbsp; "
        f"**⚡ Runtime:** {rt}  &nbsp;|&nbsp; "
        f"**📊 Pylint:** {r['pylint']:.2f}/10"
        f"{err_line}"
    )


def display_winner(results):
    if len(results) < 2:
        return ""
    r1, r2 = results[0], results[1]

    def composite(r):
        rt = (
            r["runtime_ms"]
            if isinstance(r["runtime_ms"], (int, float))
            and r["runtime_ms"] != float("inf")
            else 1e12
        )
        return (r["pass_pct"], r["pylint"], -rt)

    s1, s2 = composite(r1), composite(r2)
    if s1 == s2:
        return (
            '<div class="tie-card">'
            '<span style="font-size:2.5rem">🤝</span>'
            '<div class="winner-title" style="color:#3730a3">It\'s a Tie!</div>'
            '<div class="winner-subtitle" style="color:#4338ca">Both models performed equally across all metrics.</div>'
            "</div>"
        )

    winner = r1 if s1 > s2 else r2
    rt_str = (
        f"{winner['runtime_ms']:.1f} ms"
        if winner["runtime_ms"] != float("inf")
        else "N/A"
    )
    return (
        f'<div class="winner-card">'
        f'<span class="winner-trophy">🏆</span>'
        f'<div class="winner-title">Winner: {winner["model_name"]}</div>'
        f'<div class="winner-subtitle">Champion by composite score (Pass % → Pylint → Runtime)</div>'
        f'<div class="winner-scores">'
        f'<div class="winner-score-item">✅ Tests: {winner["pass_pct"]:.1f}%</div>'
        f'<div class="winner-score-item">📊 Pylint: {winner["pylint"]:.2f}/10</div>'
        f'<div class="winner-score-item">⚡ Runtime: {rt_str}</div>'
        f"</div></div>"
    )
