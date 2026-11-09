# LLM pytest mutation benchmark

This course project asks OpenAI to generate tests for `shipping_fee`, then checks
whether those tests detect five deliberately incorrect implementations, called
**mutants**. A mutant is **killed** when the tests detect its incorrect behavior;
it **survives** when the tests still pass.

`solution.py` is the correct implementation. `test_generated.py` is the frozen
GPT-6 Luna suite: 20 passing tests and five killed mutants (100%). The pipeline
never overwrites either file. The original specification, prompt, 2,500-token
output limit, and five mutation definitions are preserved.

## Local Gradio dashboard

The dashboard provides two separate actions:

- **Replay Frozen Tests (Free)** calls the existing evaluator on the saved
  `test_generated.py`. It needs no API key and makes no OpenAI request.
- **Generate & Evaluate (Uses API Credits)** calls `run_benchmark()` with the
  model and reasoning effort selected in the UI. It displays the fresh Python
  suite, generation time, token usage, and evaluation results without saving
  over the frozen suite.

From this project folder, install the locked dependencies:

```sh
rtk proxy uv sync --locked
```

`sync` installs the dependencies into the project's `.venv` environment;
`--locked` uses `uv.lock` and fails if it does not match `pyproject.toml`, rather
than silently changing it. This includes Gradio 6.30.0, the stable version checked
on 21 October 2026. The dependency range stays within Gradio 6; the lockfile
records the exact installed version. This command installs software but does not
call OpenAI or change the implementation/tests.

Launch the dashboard from the same folder:

```sh
rtk proxy uv run python app.py
```

Open the local URL printed in the terminal, normally
[http://127.0.0.1:7860](http://127.0.0.1:7860). The process stays running while the
dashboard is open; press **Ctrl+C** in its terminal to stop it. If the default
port is occupied, Gradio may choose another local port and print that URL.

The model defaults to `gpt-6-luna` and reasoning effort to `low`. Supported effort
settings depend on the selected model. Paid generation uses `OPENAI_API_KEY`
from the project's `.env` or terminal environment; never paste a key into the
model field. Replay ignores these settings. Missing keys, authentication/credit
issues, incomplete responses, and unexpected errors produce safe messages.
Raw API exception text is not displayed; recognized OpenAI keys and bearer
credentials are redacted from displayed code, metadata, and pytest logs.

The overview shows the correct implementation's result, mutation score, and the
source of the suite. Each mutant has a labeled status. `Not Run` means evaluation
did not reach that mutant. An invalid reference suite or any mutant evaluation
error makes the score **Unavailable**, with an explanation; valid surviving
mutants can produce a real 0%. The **Generation details** tab shows metadata,
and the collapsed **Detailed pytest logs** section retains diagnostic output.
Replay clears any code and metadata from a previous generation.

`app.py` only adapts the existing functions and result objects for display; it
does not duplicate mutation logic. Both buttons share one evaluation queue, so
only one job runs at a time. The layout wraps on narrow screens. The app uses
`gr.Blocks`; Gradio 6 theme/CSS settings are passed to `launch()`, and events use
`api_visibility="private"`. Implementation followed the official **Gradio Docs**
MCP's migration guide, layout/component reference, and event/launch APIs.
See [Gradio 6 migration guidance](https://www.gradio.app/guides/gradio-6-migration-guide)
and [Blocks and event listeners](https://www.gradio.app/guides/blocks-and-event-listeners).

**Keep this app local.** Launch explicitly uses `server_name="127.0.0.1"` and
`share=False`; analytics, monitoring, and the MCP server are disabled. Private
events hide the client API but do not replace the loopback binding as an access
boundary. Generated Python executes with your local permissions. Temporary
directories are not secure sandboxes. Do not change the binding to `0.0.0.0`,
enable sharing, put the app behind a public tunnel, or deploy it publicly.

The full test command below now also runs `test_app.py`. UI callback tests use
real frozen replay and mocked generation, check input/output connections,
redaction, errors, and local-only launch settings, and make no paid requests.

## How the pieces connect

1. `generate_tests.generate_tests(specification, source_code, model,
   reasoning_effort)` sends the unchanged prompt through the OpenAI Responses
   API. It returns a `GenerationResult`, a small named data object containing
   pytest code and generation metadata. Importing the module does not generate
   tests or require an API key.
2. `evaluate_mutants.evaluate_suite(source_code, test_code)` first evaluates the
   tests against the reference implementation (the correct code). If that run
   fails, the suite is invalid and all five mutants are marked `not_run`.
3. Once the reference passes, the evaluator applies each existing replacement
   to the original source string and runs the same tests against that mutant.
4. `benchmark.run_benchmark(...)` connects generation and evaluation and returns
   both results. `benchmark.py` provides command-line configuration and a concise
   summary, or a full JSON report (a structured text format).

The metadata records the requested model, reasoning effort, elapsed API-call
time in seconds, input/output/reasoning/total tokens, response ID, returned model,
response status, and incomplete-response reason. Missing token information is
`None` (JSON `null`), not zero. Reasoning tokens are already included in output
tokens; do not add them again to the total. See the official
[OpenAI reasoning documentation](https://developers.openai.com/api/docs/guides/reasoning).

Incomplete or empty responses raise `GenerationError`, which retains the partial
code and metadata. They do not proceed to mutation evaluation. API request errors
are also surfaced. New suites can differ between requests, even with the same
model and effort; the frozen suite is the stable regression check.

## Isolation and result reporting

`run_pytest` creates a fresh temporary directory for **each** reference or mutant
run. It writes copies of the source and test strings as `solution.py` and
`test_generated.py`, plus a local pytest configuration and `_pytest_reporter.py`.
It starts pytest with `sys.executable -m pytest`: the same Python interpreter and
installed dependencies used by the parent `uv` process. It removes inherited
pytest options, extra plugins, and Python import paths from the child environment.
The temporary directory is cleaned up automatically, including after a timeout.
Fresh folders also prevent stale bytecode from one mutant affecting another.

The small reporter is a pytest **plugin**, meaning a helper that receives pytest
events. It distinguishes assertion failures and exceptions coming from
`solution.py` from collection errors, broken fixtures, teardown errors, and
unrelated test-code runtime errors. Implementation exceptions count as behavioral
failures: for example, the existing zero-order mutant incorrectly raises
`ValueError` when the tests expect a fee. Errors in the evaluation infrastructure
never count as kills, even when pytest returns exit code 1.

Results include reference status and test counts; each mutant's `killed`,
`survived`, `error`, or `not_run` status; exit codes; timings; captured standard
output and error output; and explanatory errors. Empty suites and suites where
every test is skipped are invalid. Partial skips are allowed and are reported.
The score is a percentage, `killed / 5 * 100`, only when the reference passes and
every mutant has a conclusive result. Otherwise it is `None`; confirmed kills are
still retained. A successful evaluation can legitimately score 0%.

This is file/import isolation, not an operating-system security sandbox:
generated Python still runs with the local user's permissions. This milestone
supports only the existing self-contained `solution.py` and its five textual
mutations. Tests depending on extra files or third-party pytest plugins are not
supported. If source formatting changes so a mutation target disappears, the
evaluator reports an error instead of silently testing an unchanged implementation.

## Run through uv

Run these commands from this project folder. `rtk proxy` follows the local command
convention and forwards the command without filtering. `uv run` uses the project's
Python environment; it may install the dependencies listed in `pyproject.toml` if
they are not present. Gradio is the only new direct dependency for the dashboard;
the command-line pipeline remains available.

**Generate and evaluate a new suite:**

```sh
rtk proxy uv run python benchmark.py --model gpt-6-luna --reasoning-effort low
```

`--model` chooses the OpenAI model and `--reasoning-effort` sets its reasoning
effort. The defaults are the original `gpt-6-luna` and `low`. The model must support
the requested setting. This makes a paid OpenAI request using `OPENAI_API_KEY`
from your environment or the project's `.env`. Expect generation timing/tokens,
reference status, all five mutant results, and a score. Generated code remains in
the returned object; this command does not save over the frozen suite.

**Evaluate the frozen suite without an API request:**

```sh
rtk proxy uv run python benchmark.py --tests test_generated.py
```

`--tests` reads an existing suite and bypasses generation. Expect `20 passed` for
the reference and `5/5 = 100.0%`. The evaluator can also run directly with
`rtk proxy uv run python evaluate_mutants.py`.

Both commands accept `--timeout 30`, the time limit in seconds for each pytest
subprocess. The benchmark additionally accepts `--json`, which prints generated
code (when available), metadata, and full diagnostics. Exit code 0 means the
evaluation completed; invalid suites or generation/evaluation errors return 1.
Surviving mutants alone do not make the command fail.

**Run regression and infrastructure checks:**

```sh
rtk proxy uv run python -m pytest -q
```

`-m pytest` runs pytest through the project interpreter, and `-q` requests concise
output. This runs the frozen 20 tests, `test_pipeline.py`, and `test_app.py`. Infrastructure tests
use a fake OpenAI client and real isolated pytest subprocesses, so no API key or
paid request is needed. They check metadata, prompt preservation, invalid suites,
survivors, runtime errors, timeouts, cleanup, unchanged repository files, and the
end-to-end function wiring.

If a sandbox prevents `uv` from using its default cache, place
`--cache-dir /tmp/week4-test-generator-uv-cache` between `uv` and `run`. This changes
only uv's dependency-cache location.
