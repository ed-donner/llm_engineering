# TradeCode Arena

Compare LLMs on how safely and correctly they generate Python code for Alpaca paper trading.

## What this evaluates

TradeCode Arena tests whether a model can generate code that:

- uses Alpaca paper trading only
- fetches real AAPL data from Alpaca's latest trade endpoint
- follows one fixed buy / sell / hold strategy
- checks buying power and positions before placing an order
- handles missing credentials and API failures reasonably

It does not evaluate:

- trading profitability
- live trading readiness
- strategy quality beyond the fixed MVP rules
- multi-asset or portfolio logic

## Safety

This project is for paper trading only. It is not financial advice, and generated code must not use live Alpaca endpoints or real-money trading credentials.

## Setup

1. Create and activate a virtual environment.
2. Install the current notebook dependencies:

```bash
pip install gradio python-dotenv openai pandas
```

3. Create a `.env` file. If you add `.env.example`, use it as the template.

Example `.env.example` content:

```env
OPENROUTER_API_KEY=your_openrouter_key
ALPACA_API_KEY=your_alpaca_paper_key
ALPACA_SECRET_KEY=your_alpaca_paper_secret
ALPACA_PAPER_ENDPOINT=https://paper-api.alpaca.markets/v2
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

## Required environment variables

- `OPENROUTER_API_KEY`
- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`
- `ALPACA_PAPER_ENDPOINT`

Optional:

- `OPENROUTER_BASE_URL`

## Run the notebook

```bash
jupyter notebook app.ipynb
```

Run the cells in order, then launch the Gradio UI from the notebook output.

## Three-button flow

1. `Generate Code`: sends the fixed master prompt to one selected model and saves the script into `outputs/`.
2. `Execute Code`: runs the saved script in a subprocess with a 120-second timeout and captures `stdout`, `stderr`, exit code, and timeout state.
3. `Evaluate Model`: runs judge-based scoring plus hard caps, then appends one row to `outputs/leaderboard.csv`.

The flow is single-model and sequential by design.

## Scoring

The judge scores generated code out of 100 on:

- correct Alpaca SDK / API usage
- paper trading only
- `.env` credential usage
- AAPL strategy compliance
- latest-trade market data usage
- risk control: one order max, qty 1, no shorting
- error handling
- readability

Hard caps then reduce the score when major failures are found, including:

- live trading endpoint usage
- missing paper-trading behavior
- missing latest-trade market data
- no order submission
- possible short selling
- multiple orders per run
- missing buying-power check
- possible hardcoded API keys or secrets

If execution fails or times out, the final score is `0`.

## Leaderboard CSV

`outputs/leaderboard.csv` is append-only evaluation history.

Columns:

- `timestamp`: ISO 8601 evaluation time
- `model_label`: selected model label
- `model_id`: model ID actually called
- `final_score`: score after hard caps
- `raw_judge_score`: judge score before caps
- `status`: `Pass`, `Partial`, `Fail`, or `Execution Failed`
- `cap_reason`: cap that fired, or `—`
- `main_issue`: first issue returned by the judge

The Gradio leaderboard view sorts by `final_score` descending.

## Known limitations

- The app is notebook-first, not yet packaged as a standalone app.
- Model and judge behavior depend on external APIs.
- Static checks are heuristic and can produce false positives or false negatives.
- The project compares code suitability, not trading performance.

## Future improvements

- add `requirements.txt` and `.env.example` to the repo
- extract notebook helpers into Python modules
- improve judge output validation and cap diagnostics
- add notebook-independent automated tests
- support a cleaner evaluation history and export workflow
