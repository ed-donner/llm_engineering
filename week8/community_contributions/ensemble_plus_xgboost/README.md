# Ensemble + XGBoost (Week 8 — Option 1)

**Same “Price is Right” pipeline, one twist:** add an **XGBoost-on-embeddings** pricer to the ensemble and compare error with/without it.

## What’s in this folder

| File | Purpose |
|------|--------|
| `train_xgboost.py` | Train XGBRegressor on (embedding of product summary → price) using `ed-donner/items_lite`; saves `xgboost_pricer.pkl`. |
| `xgboost_agent.py` | Agent that loads the encoder + saved model and exposes `price(description) -> float`. |
| `ensemble_plus.py` | Ensemble that adds XGBoost to the course mix: **0.7× Frontier + 0.1× Specialist + 0.1× NN + 0.1× XGBoost** (so XGB is the new member). |
| `compare_light.py` | Lightweight comparison **without** Modal/DNN: **Frontier-only** vs **Frontier + XGBoost** (0.8 frontier, 0.2 xgb) on the test set. |

## Quick run (light comparison, no Modal/DNN)

Run everything from **this directory** (`ensemble_plus_xgboost`). No need to `cd` into `week8`.

1. **Train XGBoost** (needs `HF_TOKEN`, uses ~10k train items):

   ```bash
   uv run python train_xgboost.py
   ```

2. **Build Chroma** (if you haven’t already): run Week 8 Day 2 cells that create `week8/products_vectorstore` and populate the `products` collection.

3. **Run comparison** (needs `OPENAI_API_KEY` and Chroma at `week8/products_vectorstore`):

   ```bash
   uv run python compare_light.py
   ```

   This runs the course evaluator twice (Frontier-only, then Frontier + XGBoost) and shows charts/reports so you can see whether adding XGBoost improves average error.

   You can also open `compare.ipynb` and run all cells from this folder; paths are resolved automatically.

## Full ensemble (with Modal + DNN)

If you have the **Modal pricer** and **deep_neural_network.pth** in `week8`:

- Use `EnsembleAgentPlus` from `ensemble_plus.py` in your `DealAgentFramework` (or in a small script that builds the planner with `EnsembleAgentPlus(collection)` instead of `EnsembleAgent(collection)`).
- Weights there: 0.7 frontier, 0.1 specialist, 0.1 neural_network, 0.1 xgboost.

## Dependencies

- `sentence-transformers`, `chromadb`, `openai`, `xgboost`, `joblib`, `huggingface_hub`, `python-dotenv` (and the rest of the course `week8` stack).  
- For training: `xgboost`; the course `agents.items` and `agents.evaluator` for compare.

## Summary

- **Option 1** = add one extra pricer (XGBoost on embeddings) and compare with/without it.  
- **Light path** = Frontier vs Frontier+XGBoost (no Specialist/Modal, no DNN).  
- **Full path** = use `EnsembleAgentPlus` in the framework for the full ensemble including the new member.
