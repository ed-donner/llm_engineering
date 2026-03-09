# 🎬 Movie & Book Review Sentiment + Rating Predictor

Fine-tuning **LLM** with **QLoRA** to predict sentiment and star ratings from natural language reviews.

---

## ⚠️ Disclaimer

This model was fine-tuned on **Yelp restaurant reviews** using a small dataset of 10,000 samples for 1 epoch on a free Google Colab T4 GPU. It is a **portfolio/learning project** and not a production-grade sentiment analysis system.

- Predictions may be inaccurate on reviews outside the Yelp domain (movies, books, products)
- The model has not been evaluated for bias across languages, demographics, or review styles
- Do not use for commercial or high-stakes decision making
- Results may vary depending on review length, writing style, and domain

---

## Results

| Metric | Base Model (zero-shot) | Fine-tuned |
|---|---|---|
| Sentiment Accuracy | 0% | **84.6%** |
| Rating MAE | — | **0.349 stars** |
| Parse Rate | 0% | **99.8%** |

The base model produced **zero parseable outputs** — it ignored the format entirely. After fine-tuning on 10,000 Yelp reviews, the model correctly structures its response 99.8% of the time with 84.6% sentiment accuracy.

### Evaluation Details

- **Eval size:** 500 test samples
- **Dataset:** Yelp Review Full (held-out test set)
- **Sentiment Accuracy:** % of predictions matching the correct Positive/Negative/Mixed label
- **Rating MAE:** Mean Absolute Error between predicted and true star rating (1–5 scale) — 0.349 means the model is on average **less than half a star off**
- **Parse Rate:** % of outputs that followed the expected format and could be parsed

---
