# Week 7 — Few-Shot Price Predictor

Week 7 covers fine-tuning Llama 3.2-3B with QLoRA on Amazon product data (requires a GPU on Google Colab).

This notebook replicates the core idea locally using **few-shot prompting** — showing the LLM example price pairs before asking it to predict, which mirrors what fine-tuning does by exposing the model to training examples.

## What it compares

| Approach | How it works |
|----------|-------------|
| Baseline | Always guesses the average price |
| Zero-shot | Asks GPT-4o-mini with no examples |
| Few-shot | Shows GPT-4o-mini 5 example pairs first, then asks |

## Why few-shot relates to fine-tuning

Fine-tuning bakes training examples into the model weights. Few-shot prompting puts those same examples in the context window. Both expose the model to real price data — few-shot is just the lightweight, no-GPU version of the same idea.

## Setup

Add your OpenAI API key to `.env`:

```
OPENAI_API_KEY=sk-...
```

Install dependencies:

```bash
pip install openai gradio datasets python-dotenv tqdm
```

## Usage

Run all cells in `few_shot_pricer.ipynb` top to bottom. The Gradio UI at the end lets you toggle between zero-shot and few-shot mode to see the difference live.
