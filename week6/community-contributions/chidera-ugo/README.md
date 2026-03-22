# The Price Is Right — Simplified

A simplified version of the Week 6 capstone project. Given an Amazon product description, predict its price using GPT-4o-mini and compare it against a naive baseline.

## What it does

1. Loads Amazon Appliances product data from HuggingFace
2. Cleans and filters items to those with valid prices ($1–$1000) and real descriptions
3. Runs two price predictors on a 50-item sample:
   - **Baseline** — always guesses the average price
   - **LLM** — asks GPT-4o-mini to predict the price from the description
4. Compares both using Mean Absolute Error (MAE)
5. Launches a Gradio UI to test with any product description

## Setup

Make sure you have your `.env` file with your OpenAI API key:

```
OPENAI_API_KEY=sk-...
```

Install dependencies if needed:

```bash
pip install openai gradio datasets python-dotenv tqdm
```

## Usage

Run all cells in `price_predictor.ipynb` top to bottom.

The Gradio UI will launch at the end — paste any Amazon product description to get a predicted price.

## Example output

```
========================================
  Baseline MAE : $98.43
  LLM MAE     : $41.22
  Improvement  : 58.1%
========================================
```
