# TradeCode Arena — compare LLM-generated Alpaca paper trading code

## Overview

TradeCode Arena tests how safely LLMs generate Python code for Alpaca paper trading.
Use it to generate, run, score, and compare single-model trading scripts.

## Features

- Generate Python trading scripts with OpenRouter models.
- Execute saved scripts in a subprocess.
- Score code with judge-based evaluation.
- Apply hard caps for unsafe trading behavior.
- Append results to a leaderboard CSV.
- Run everything from a Gradio notebook UI.

## Installation

```bash
uv pip install gradio python-dotenv openai pandas
```

## Usage

Run the notebook, then use the Gradio buttons in order.

1. `Generate Code`
2. `Execute Code`
3. `Evaluate Model`

Results are saved in `outputs/leaderboard.csv`.

## Configuration

| Name                    | Default                               | What it does                          |
| ----------------------- | ------------------------------------- | ------------------------------------- |
| `OPENROUTER_API_KEY`    | none                                  | Authenticates OpenRouter model calls. |
| `ALPACA_API_KEY`        | none                                  | Authenticates Alpaca paper trading.   |
| `ALPACA_SECRET_KEY`     | none                                  | Authenticates Alpaca paper trading.   |
| `ALPACA_PAPER_ENDPOINT` | `https://paper-api.alpaca.markets/v2` | Sets Alpaca paper endpoint.           |
| `OPENROUTER_BASE_URL`   | `https://openrouter.ai/api/v1`        | Sets OpenRouter API base URL.         |
