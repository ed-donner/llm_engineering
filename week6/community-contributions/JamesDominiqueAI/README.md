# Car Price Predictor — Fine-tuned GPT-4.1-nano

> Predict used car prices on the Russian market from a plain-text description,
> using a fine-tuned variant of OpenAI's GPT-4.1-nano.

## Disclaimer

**Please read before using this model in any real-world context.**

### Model limitations

This project uses **GPT-4.1-nano**, OpenAI's smallest and lightest model in the
GPT-4.1 family. It was chosen deliberately for cost and speed during
experimentation — not for maximum accuracy. A larger model such as GPT-4.1-mini
or GPT-4o would produce meaningfully better results on this task.

### Dataset limitations

The model was fine-tuned on **2,000 examples** drawn from the
[imbalet/used_cars](https://huggingface.co/datasets/imbalet/used_cars) dataset,
which contains ~432,000 Russian used car listings. Using only 2,000 of 432,000
available rows (less than 0.5%) was a deliberate trade-off to keep fine-tuning
costs under $1 and training time under 30 minutes.

As a result:

- The model has **not seen most car makes, regions, or price ranges** in the dataset
- Predictions for rare cars, very cheap (<₽300k) or very expensive (>₽5M) vehicles are unreliable
- The model reflects **Russian market prices at the time the dataset was scraped** — prices will have changed
- Prices are in **Russian rubles (₽)** and are not adjusted for inflation or exchange rates


**63% accuracy** means 63 out of 100 predictions fall within ±20% of the actual
price. For a ₽1,500,000 car, the model typically predicts between
₽1,200,000 and ₽1,800,000.

For context, XGBoost trained on the full 345,000-row dataset achieves ~72%.
Professional pricing platforms (Auto.ru, Avito) achieve ~85–90% using millions
of listings, photos, and real-time market data.

---

## 🗂️ Larger Datasets to Improve This Model

If you want to push accuracy beyond 63%, here are the best datasets available,
ordered by relevance:

### 🇷🇺 Russian market (same domain as this project)

| Dataset | Rows | Source | Notes |
|---------|------|--------|-------|
| [imbalet/used_cars](https://huggingface.co/datasets/imbalet/used_cars) | 432,000 | Hugging Face | Already used — just use **all** rows instead of 2,000 |
| [Shikivvs1/car-sales-dataset](https://huggingface.co/datasets/Shikivvs1/car-sales-dataset) | varies | Hugging Face | Russian car sales data |

**Quickest win:** change `FINE_TUNE_TRAIN_SIZE = 2000` to `FINE_TUNE_TRAIN_SIZE = 20000`
in the current code. This uses the same dataset you already have and costs ~$4.
Expected accuracy improvement: **+10–15pp** (estimated 73–78%).
