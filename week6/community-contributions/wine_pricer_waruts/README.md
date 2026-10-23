# The Pour Is Right: a wine pricer, weeks 6 to 8

My version of the "Price Is Right" capstone, applied to wine. Models predict the price of a bottle from its review, and an agent system finds real wine deals online and sends alerts to Telegram.

Weeks 6 and 7 are in this folder's first pull request; week 8 (the agents and the app) is in a second one, to keep each under 2,000 lines.

By Emmanuel Wachira ([wachira7](https://github.com/wachira7)).

## Data

- Source: [spawn99/wine-reviews](https://huggingface.co/datasets/spawn99/wine-reviews), 280,901 Wine Enthusiast reviews.
- Curated to 22,000 wines (20,000 train, 1,000 validation, 1,000 test): deduplicated (the dataset merges two overlapping scrapes, so about 111,000 rows were repeats), \$4 to \$200, sampled with weight `p**0.5` to keep prices realistic (average \$41).
- Rewritten into a fixed six-line summary (Wine, Style, Origin, Points, Tasting, Verdict) with `gpt-oss-20b` on the Groq Batch API, for about \$1. The rewrite also removes price hints: wines whose text mentioned price or value went from 693 to 49.
- Published as [Warumanu/wines_lite](https://huggingface.co/datasets/Warumanu/wines_lite) and, as prompts for fine-tuning, [Warumanu/wines_prompts_lite](https://huggingface.co/datasets/Warumanu/wines_prompts_lite).

## Results

Average absolute error on the same 200 test wines (median price \$33).

| Model | Error |
|---|---|
| Constant (training average) | \$21.71 |
| Linear regression on points and text length | \$16.46 |
| Bag of words + linear regression | \$13.50 |
| XGBoost | \$11.67 |
| Deep neural network (residual, log-price target) | \$11.23 |
| GPT-4.1 Nano, zero-shot | \$15.10 |
| Qwen 3.8 27B, zero-shot | \$14.42 |
| Claude Sonnet 5, zero-shot | \$9.06 |
| Qwen 3 4B base, 4-bit | \$23.15 |
| **Qwen 3 4B, QLoRA fine-tuned** | **\$10.10** |
| Qwen 3.8 27B with RAG | \$9.96 |
| GPT-5.1 with RAG | \$8.87 |
| Claude Sonnet 5 with RAG | \$8.25 |
| **Ensemble** (0.8 RAG, 0.1 fine-tuned, 0.1 neural network) | **\$7.96** |

## The agent system

```
ScannerAgent (WTSO, Last Bottle, HotUKDeals) -> GPT-5-mini, structured outputs
      |
LangGraph planner: scan -> price each deal (fan-out) -> decide -> notify (optional approval)
      |
EnsembleAgent
  - FrontierAgent: Qdrant RAG (5 similar wines) + Claude Sonnet 5
  - SpecialistAgent: fine-tuned Qwen 3 4B on Modal (T4)
  - NeuralNetworkAgent: the week 6 deep neural network
      |
MessagingAgent -> Telegram bot
```

`pour_is_right.py` is the Gradio app: it runs the planner every hour or on demand, with live logs and a 3D map of the vector store.

## Where this differs from the course

- **Qwen 3 4B Base** for fine-tuning: Llama 3.2 3B is gated. Qwen writes prices one digit per token, so generation allows 8 new tokens.
- **Free Colab T4**: training needs `float16` with the LoRA weights kept in `float32`. `bf16` ran six times slower on a T4.
- **Qdrant** (local mode) instead of Chroma, including filtered search on country and price.
- **Telegram** instead of Pushover.
- **Wine sources**: DealNews has no wine, so the scanner reads WTSO and Last Bottle (US) and HotUKDeals (UK, converted from pounds).
- **Alert threshold**: estimate at least 30% and \$10 above the price, instead of a fixed \$50 gap.
- **A third planner in LangGraph**, beside the fixed and the tool-calling versions: typed state, conditional edges, `Send` fan-out with a reducer, and `interrupt()` for human approval.
- **OpenAI fine-tuning (week 6 day 5) is left out**: OpenAI has closed self-serve fine-tuning to new organisations.

## Files

| Week | Files |
|---|---|
| 6 | `day1` to `day4` notebooks, `pricer/` |
| 7 | `week7_day2.ipynb` (prompts, local), `week7_colab_1` to `3` (base model, training, evaluation; run on Colab) |
| 8 | `week8_day1` to `day5`, `week8_day4_langgraph.ipynb`, `agents/`, `pricer_service.py`, `deal_agent_framework.py`, `pour_is_right.py` |

## Running it

Keys in the repo's `.env`: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `HF_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. Modal needs `modal token new` and a secret named `huggingface-secret`.

Run the notebooks in order from this folder. The week 7 Colab notebooks expect `HF_TOKEN` in Colab's secrets. Then `python pour_is_right.py` starts the app.

Costs: the Groq batch rewrite was about \$1, QLoRA training was free on Colab, and each 200-wine evaluation or agent run costs cents.
