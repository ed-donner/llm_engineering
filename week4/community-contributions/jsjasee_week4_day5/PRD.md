# TradeCode Arena — MVP Build Plan (v2)

## Project Summary

**TradeCode Arena** is a small Gradio-based learning project that compares multiple LLMs on their ability to generate safe, correct Python code for Alpaca paper trading.

The project is not trying to discover the best trading strategy. It is trying to answer a narrower AI engineering question:

> Which LLM generates the most suitable Alpaca paper-trading code when given the same trading-code prompt?

The generated code will use Alpaca paper trading, fetch real AAPL market data via the **latest trade** endpoint, decide whether to buy, sell, or do nothing, and submit a paper order only if the strategy condition is met.

The leaderboard score represents **code suitability for safe paper-trading automation**, not trading skill or profitability.

---

## Core MVP Decisions

| Area                  | Decision                                                                 |
| --------------------- | ------------------------------------------------------------------------ |
| Broker API            | Alpaca paper trading                                                     |
| Market data           | Real Alpaca market data, **latest trade** endpoint                       |
| Trading mode          | Full paper execution                                                     |
| Execution style       | Manual, one model at a time, three-button Gradio flow                    |
| Stock                 | Fixed to `AAPL`                                                          |
| Strategy              | Fixed threshold strategy for MVP                                         |
| Models                | 3–5 OpenRouter models, configurable by dictionary                        |
| Judge                 | One configurable judge LLM via OpenRouter, default `openai/gpt-5`        |
| Evaluation            | Substring/regex static checks + LLM judge                                |
| Error handling        | If generated code fails execution, final score is 0                      |
| Subprocess timeout    | **120 seconds**                                                          |
| Output                | Gradio UI + saved generated scripts + `outputs/leaderboard.csv` (append) |
| Environment variables | Read from `.env`                                                         |
| Project format        | Jupyter notebook + helper files + output folder                          |

---

## Important Safety Boundary

This project must use **Alpaca paper trading only**.

The generated code must not use live trading credentials, live trading endpoints, or real-money execution.

The master prompt, evaluator, and judge rubric should all treat live-trading behavior as a major failure.

---

## Expected `.env` Variables

```

OPENROUTER_API_KEY=your_openrouter_key

ALPACA_API_KEY=your_alpaca_paper_key

ALPACA_SECRET_KEY=your_alpaca_paper_secret

ALPACA_PAPER_ENDPOINT=https://paper-api.alpaca.markets

```

Optional:

```

OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

```

The judge uses the **same OpenAI-compatible OpenRouter client** — no separate `OPENAI_API_KEY` needed.

---

## Fixed MVP Trading Strategy

Every model generates code for the same strategy.

### Strategy

- Trade only `AAPL`.
- Fetch the latest real AAPL price via Alpaca's **latest trade** endpoint.
- If the latest AAPL price is below `180`:
  - Check Alpaca account **buying power**.
  - If sufficient, buy `1` share. If not, skip and log reason.
- If the latest AAPL price is above `190`:
  - Query current **positions**.
  - If 1+ AAPL shares are held, sell `1` share.
  - If 0 shares held, skip and log reason. **Never short.**
- Otherwise, do nothing.
- If US market is closed, still proceed using the last available trade price.
- Use Alpaca paper trading only.
- Use `.env` variables for credentials.
- Place at most one order per script run.
- Print useful output showing:
  - latest trade price
  - decision made
  - precondition checks (positions / buying power)
  - whether an order was submitted
  - order response or error message

### Why fixed strategy first?

A fixed strategy makes model comparison fair. Differences in score come from code quality, instruction-following, and API correctness — not different user inputs.

---

## MVP User Flow (sequential, one model at a time)

1. User opens the Gradio app.
2. User selects **one** OpenRouter model from a dropdown.
3. User clicks **Generate Code**.
   - Same master prompt is sent to that single model.
   - Generated code is displayed in a code box.
   - Generated code is saved to `outputs/generated_<model_label>.py`.
4. User reviews the generated code.
5. User clicks **Execute Code**.
   - The script runs in a subprocess with a 120s timeout.
   - stdout, stderr, and exit code are captured and shown.
6. User clicks **Evaluate Model**.
   - Substring/regex static checks run on the generated code.
   - Judge LLM reviews code + execution output + static check result.
   - Hard caps are applied.
   - A new row is appended to `outputs/leaderboard.csv`.
   - The leaderboard table refreshes from the CSV.
7. User repeats with a different model selection.

---

## Proposed Project Structure

```
tradecode-arena/
app.ipynb
helpers/
model_[client.py](http://client.py)
[prompts.py](http://prompts.py)
[evaluator.py](http://evaluator.py)
[runner.py](http://runner.py)
file_[utils.py](http://utils.py)
outputs/
generated_<model_label>.py
leaderboard.csv
.env
.env.example
requirements.txt
[README.md](http://README.md)
```

---

# Phase 1 — Set Up Project Skeleton

## Goal

Create the basic folder structure and confirm the notebook can import helper functions.

## Tasks

- Create project folder.
- Create `app.ipynb`.
- Create `outputs/` folder.
- Create `requirements.txt`.
- Create helper files.
- Confirm Python can load environment variables from `.env`.

## Checklist

- [ ] `app.ipynb` exists.
- [ ] `.env` exists locally with OpenRouter + Alpaca paper credentials.
- [ ] `.env.example` exists without real secrets.
- [ ] `outputs/` folder exists.
- [ ] Notebook can read `OPENROUTER_API_KEY`.
- [ ] Notebook can read Alpaca paper credentials.

## Suggested requirements

```

gradio

python-dotenv

openai

pandas

alpaca-py

```

---

# Phase 2 — Define Model Configuration

## Goal

One central place to configure the candidate models and the judge.

## Example

```

MODELS = {

"GPT model": "openai/gpt-5",

"Claude model": "anthropic/claude-sonnet-4.5",

"Qwen model": "qwen/qwen-2.5-coder",

}

DEFAULT_JUDGE_MODEL = "openai/gpt-5"

```

## Checklist

- [ ] Model dict is easy to edit.
- [ ] Each model has a display label and an OpenRouter model ID.
- [ ] Judge model is configurable via global variable `JUDGE_MODEL`.
- [ ] Gradio dropdown reads from `MODELS`.

---

# Phase 3 — Write the Master Code-Generation Prompt

## Goal

A precise prompt that produces consistent, comparable Alpaca paper-trading code across models.

## Master Prompt Requirements

The generated code must:

- Be valid Python.
- Use Alpaca paper trading only.
- Use real Alpaca market data via the **latest trade** endpoint specifically.
- Fetch the latest AAPL trade price.
- Use `.env` credentials with the exact variable names listed.
- Submit at most one paper order per run.
- If price < 180:
  - Query account **buying power**.
  - Buy 1 AAPL share only if sufficient buying power; otherwise skip and log.
- If price > 190:
  - Query current **positions**.
  - Sell 1 AAPL share only if at least 1 AAPL share is held; otherwise skip and log.
  - **Never short.**
- Otherwise do nothing.
- If US market is closed, proceed using the last available trade price.
- Print: latest price, decision, precondition checks, order result or error.
- Handle missing credentials gracefully.
- Handle API errors gracefully.
- Avoid infinite loops or repeated polling.
- Avoid hardcoded API keys.
- Avoid live trading endpoints.
- Avoid portfolio-wide logic.
- Avoid any ticker except AAPL.
- Return code only — no markdown fences, no commentary.

## Checklist

- [ ] Prompt specifies `AAPL`.
- [ ] Prompt specifies buy threshold `180` and sell threshold `190`.
- [ ] Prompt specifies quantity `1`.
- [ ] Prompt says paper trading only.
- [ ] Prompt provides exact env variable names.
- [ ] Prompt specifies **latest trade** endpoint by name.
- [ ] Prompt requires buying-power check before buy.
- [ ] Prompt requires position check before sell, no shorting.
- [ ] Prompt allows execution when market is closed using last available price.
- [ ] Prompt says return Python code only.

---

# Phase 4 — Generate Code from One OpenRouter Model

## Goal

Send the master prompt to the **single selected** model and capture the generated code.

## Tasks

- Build `generate_code(model_id, prompt) -> str`.
- Call OpenRouter using the selected model ID.
- Strip markdown code fences if a model returns them.
- Surface API errors clearly in Gradio without crashing the app.

## Checklist

- [ ] Single OpenRouter call works end-to-end.
- [ ] Generated code returned as plain string.
- [ ] Code fences/backticks STRIPPED if present.
- [ ] API errors shown in the UI, app stays alive.

---

# Phase 5 — Save Generated Scripts

## Goal

Save the generated code to `outputs/` for execution and audit.

## Tasks

- Build a safe filename from the model label, e.g. `outputs/generated_gpt_model.py`.
- Save generated code as `.py`.
- Overwrite the previous file for the same model when re-generating (deliberate).
- Return the file path for the runner.

## Checklist

- [ ] Each generated script is saved.
- [ ] Filename is safe and predictable from model label.
- [ ] File path is stored in app state for the runner.

---

# Phase 6 — Build the Gradio UI (sequential single-model flow)

## Components

### Inputs

- Model dropdown (single select)
- Judge model textbox (defaults to `JUDGE_MODEL` from `.env`)
- **Generate Code** button
- **Execute Code** button (enabled after Generate)
- **Evaluate Model** button (enabled after Execute)

### Outputs

- Generated code display
- Execution stdout/stderr/exit-code box
- Static check result panel
- Judge feedback panel
- Final score display
- Leaderboard dataframe (read from `outputs/leaderboard.csv`)

## Checklist

- [ ] User can select one model.
- [ ] Generate / Execute / Evaluate buttons are sequential and clearly labeled.
- [ ] Each button updates the correct UI region without resetting prior state.
- [ ] Leaderboard renders from CSV via `pandas.read_csv` → `gr.Dataframe`.
- [ ] Empty leaderboard handled (first run, no CSV yet).

---

# Phase 7 — Run Generated Scripts Manually from Gradio

## Goal

Execute the saved generated script in a subprocess.

## Constraints

- Use the **same Python interpreter / venv** as the notebook (resolve via `sys.executable`).
- Working directory = project root (so `python-dotenv` finds `.env`).
- **Timeout: 120 seconds.**
- Capture stdout, stderr, exit code.
- Show all three in the Gradio output box.

## Execution Result Shape

```

{

"stdout": "...",

"stderr": "...",

"exit_code": 0,

"timed_out": False

}

```

## Checklist

- [ ] Subprocess uses `sys.executable`.
- [ ] cwd is project root.
- [ ] 120s timeout enforced via `subprocess.run(..., timeout=120)`.
- [ ] `TimeoutExpired` caught and surfaced as `timed_out: True`.
- [ ] stdout/stderr displayed even on non-zero exit code.

---

# Phase 8 — Rule-Based Static Evaluation

## Goal

Cheap, fast substring/regex checks before invoking the judge.

## Implementation

Substring / regex matching on the generated source string. Document the patterns explicitly in `evaluator.py` so they can be tightened later.

## Static Checks

| Check                 | Pattern hint                                        |
| --------------------- | --------------------------------------------------- |
| Alpaca usage          | `alpaca` import or `paper-api.alpaca.markets` URL   |
| Paper trading         | `paper-api.alpaca.markets` or `paper=True`          |
| Env vars              | `os.environ` / `getenv` / `dotenv` reference        |
| Latest trade endpoint | `latest_trade` or `/v2/stocks/AAPL/trades/latest`   |
| Order submission      | `submit_order` / `/v2/orders` POST                  |
| Position check        | `get_position` / `list_positions` / `/v2/positions` |
| Buying-power check    | `buying_power` reference                            |
| AAPL only             | `"AAPL"` literal, no other ticker symbols           |
| Quantity 1            | `qty=1` / `quantity=1` (not larger)                 |
| No live endpoint      | absence of `api.alpaca.markets` (live URL)          |
| Error handling        | `try` / `except` present                            |

## Checklist

- [ ] Static evaluator accepts code string.
- [ ] Returns structured dict of pass/fail per check.
- [ ] Records missing items into a list.
- [ ] Result is fed into the judge prompt and the cap logic.

---

# Phase 9 — Hard Score Caps

## Goal

Strict ceilings so a polished-looking but unsafe script cannot score high.

## Hard Caps

| Condition                                           | Final score cap |
| --------------------------------------------------- | --------------: |
| Generated code fails to execute                     |               0 |
| Code attempts live trading (live endpoint detected) |              20 |
| Code does not use paper trading                     |              20 |
| Code does not fetch real market data                |              40 |
| Code does not submit or prepare an Alpaca order     |              60 |
| Code trades any ticker other than AAPL              |              60 |
| Code shorts AAPL (sells without checking position)  |              60 |
| Code can place more than one order per run          |              70 |
| Code submits buy without checking buying power      |              70 |
| Code hardcodes API keys                             |              70 |

## Notes

- If execution fails, final score is exactly `0`.
- If multiple caps apply, use the **lowest**.
- Cap reason is recorded as a single short string for the CSV.

## Checklist

- [ ] Execution failure forces score 0.
- [ ] Live-trading detection caps at 20.
- [ ] Shorting detection caps at 60.
- [ ] Missing buying-power check caps at 70.
- [ ] Lowest cap wins when multiple apply.
- [ ] Cap reason string surfaces in `cap_reason` column.

---

# Phase 10 — LLM Judge Evaluation

## Goal

Use one configurable judge LLM (via OpenRouter) to score the generated code.

## Judge Input

- Master prompt
- Generated code
- Execution stdout / stderr / exit code
- Static check results
- Hard cap result (if any)

## Judge Output (JSON)

```

{

"raw_score": 85,

"strengths": [

"Uses Alpaca paper trading",

"Fetches latest trade via correct endpoint",

"Reads credentials from .env"

],

"issues": [

"Buying-power check missing",

"Error handling could be clearer"

],

"summary": "Mostly suitable; one risk control missing."

}

```

> `verdict` field is intentionally **dropped**. Status is derived from final score in the leaderboard.

## Judge Rubric

| Category                                          |  Points |
| ------------------------------------------------- | ------: |
| Correct Alpaca SDK / API structure                |      20 |
| Uses paper trading only                           |      20 |
| Uses `.env` credentials correctly                 |      15 |
| Follows AAPL buy/sell strategy with preconditions |      15 |
| Uses real market data (latest trade)              |      10 |
| Risk control: ≤1 order, qty 1, no shorting        |      10 |
| Handles errors / missing credentials              |       5 |
| Code readability                                  |       5 |
| **Total**                                         | **100** |

## Checklist

- [ ] Judge prompt embeds full rubric.
- [ ] Judge receives execution output.
- [ ] Judge returns valid JSON; invalid JSON falls back to a default error result.
- [ ] `raw_score` stored separately from `final_score`.
- [ ] Hard cap applied after judge score.

---

# Phase 11 — Leaderboard CSV

## File

`outputs/leaderboard.csv` — append-only, full history of evaluations.

## Columns

| Column            | Meaning                                                               |
| ----------------- | --------------------------------------------------------------------- |
| `timestamp`       | ISO 8601 timestamp of the evaluation                                  |
| `model_label`     | Display name from `MODELS` dict                                       |
| `model_id`        | OpenRouter model ID actually called                                   |
| `final_score`     | Score after hard caps                                                 |
| `raw_judge_score` | Score the judge gave before caps (diagnostic)                         |
| `status`          | Pass / Partial / Fail / Execution Failed (derived from `final_score`) |
| `cap_reason`      | Which cap fired, or `"—"` if none                                     |
| `main_issue`      | First / most critical item from judge `issues` array                  |

## Status Rules

| `final_score` | `status`         |
| ------------: | ---------------- |
|        80–100 | Pass             |
|         60–79 | Partial          |
|          1–59 | Fail             |
|             0 | Execution Failed |

## Checklist

- [ ] CSV is created with header row on first write.
- [ ] Each Evaluate Model click appends exactly one row.
- [ ] Re-running the same model adds a new row (history preserved).
- [ ] Gradio dataframe sorts by `final_score` descending by default.
- [ ] Empty / missing CSV handled cleanly on first launch.

---

# Phase 12 — README

## Sections

- Project title and one-line description
- What the project evaluates (and what it does not)
- Setup instructions
- Required `.env` variables
- How to run the notebook
- The three-button flow: Generate → Execute → Evaluate
- How scoring works (rubric + hard caps)
- Safety note: paper trading only
- Known limitations
- Future improvements

## Checklist

- [ ] README states paper trading only, not financial advice.
- [ ] README explains the three-button single-model flow.
- [ ] README documents `outputs/leaderboard.csv` columns.
- [ ] README includes `.env.example`.
- [ ] README includes setup steps.

---

# Final MVP Acceptance Criteria

- [ ] User can select one OpenRouter model.
- [ ] Generate Code button sends master prompt and saves output to `outputs/`.
- [ ] Execute Code button runs the saved script with a 120s timeout and shows stdout/stderr/exit code.
- [ ] Evaluate Model button runs static checks, calls judge, applies hard caps, and appends a row to `outputs/leaderboard.csv`.
- [ ] Leaderboard dataframe renders sorted by `final_score`.
- [ ] Project uses fixed AAPL strategy, latest-trade endpoint, paper trading only.
- [ ] Generated code performs position and buying-power checks.
- [ ] Hard caps include: live trading, shorting, no buying-power check.
- [ ] README explains the project and safety boundaries.

---

# Out of Scope for MVP

- Real-money trading
- Profit-based ranking
- Multi-day tournaments
- Backtesting engine
- Portfolio optimization
- Multiple tickers
- Parallel multi-model generation
- User accounts / DB
- Streaming market data
- Strategy customization UI
- Deployment

---

# Future Improvements

- Configurable ticker
- Configurable thresholds
- Dry-run mode
- Backtest comparison
- AST-based static analysis
- Subprocess sandboxing
- Cost / latency / token-usage tracking per model
- Multiple judge models with disagreement reporting
- Human override score
- CSV → chart visualization in the leaderboard tab

---

# Recommended Build Order

1. `.env` and credential loading.
2. One OpenRouter call with hardcoded prompt.
3. Master prompt with all strategy + safety bullets.
4. Single-model code generation in notebook.
5. Save generated code to `outputs/`.
6. Display generated code in Gradio.
7. Add Execute Code button + 120s subprocess runner.
8. Add static checks (substring/regex).
9. Add judge LLM call.
10. Add hard caps and final-score computation.
11. Append to `outputs/leaderboard.csv` and render dataframe.
12. README and `.env.example`.

---

# Final Project Definition

**TradeCode Arena** is a Gradio + Jupyter tool that benchmarks OpenRouter LLMs on their ability to generate safe, correct Python code for Alpaca paper trading. Each selected model receives the same master prompt for a fixed AAPL threshold strategy with explicit position and buying-power preconditions. The app saves the generated script, lets the user manually run it against Alpaca paper trading with a 120-second timeout, captures execution output, evaluates the result with substring static checks and a configurable judge LLM via OpenRouter, applies strict hard score caps, and appends each result as a row in `outputs/leaderboard.csv` rendered as a sortable Gradio dataframe.
