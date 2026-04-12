# Price Prediction Experiments

A set of experiments exploring how much pricing signal can be extracted from Amazon product
descriptions, starting from a tiny GPT trained from scratch and ending with a RAG + frontier
LLM ensemble.

**Experiment 1 — Baby GPT**: A 7M-parameter vanilla GPT trained from scratch on 16k clothing
items, classifying into 5 price buckets. Uses an autonomous autoresearch-style loop (agent
trains, evaluates, and iterates overnight). Best result: 0.2448 macro-averaged accuracy vs 0.20
random baseline. A TF-IDF + Logistic Regression baseline beats it by 16pp in 5 seconds on CPU.

**Experiment 2 — RAG + Ensemble**: GPT 5.1 retrieval-augmented generation over a 400k-item
ChromaDB vectorstore, combined with a fine-tuned Llama 3.2-3B specialist (via Modal) and a DNN.
Experiments with category-aware retrieval and alternative embedding models. Best result: $29.30
MAE (first price buckets run) vs the course's $29.90 — marginally better, though on a 200-item
sample the margin is within noise and the result wasn't reproducible in later runs.

**Key finding**: The hard items (niche products priced by brand reputation rather than
description text) set a floor that no retrieval improvement can move. The remaining error is in
the data, not the model.

→ [github.com/ElizaZadura/BabyGPTPriceExperiment](https://github.com/ElizaZadura/BabyGPTPriceExperiment)
