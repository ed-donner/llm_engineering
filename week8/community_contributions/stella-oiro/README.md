---
title: stella-oiro
app_file: app.py
sdk: gradio
sdk_version: 5.49.1
---
# Multi-Agent Clinical Triage System — Week 8

A multi-agent system for emergency department triage that combines a fine-tuned offline model, RAG over clinical guidelines, and a frontier LLM — orchestrated by an autonomous planning agent.

## What it does

Takes a clinical presentation and routes it through an ensemble of three specialised agents, each bringing a different source of intelligence:

| Agent | Method | Notes |
|---|---|---|
| SpecialistAgent | Fine-tuned Llama 3.2 3B (Week 7) deployed on Modal | Runs offline, no data leaves the hospital |
| RAGAgent | ChromaDB + clinical guidelines + GPT-4.1-mini | Retrieves relevant protocols before classifying |
| FrontierAgent | GPT-4.1-mini zero-shot | Fast, high-quality baseline |
| EnsembleAgent | Weighted vote across all three | Final triage decision |
| MessengerAgent | Pushover push notification | Alerts on-call doctor for Immediate cases |
| AutonomousAgent | GPT-4.1-mini with tool calling | Orchestrates the pipeline end-to-end |

## Why this matters

Each week builds on the last:
- **Week 5**: Built RAG over clinical guidelines
- **Week 7**: Fine-tuned Llama for triage (runs offline)
- **Week 8**: Deploy fine-tuned model on Modal, wire all agents into an autonomous system

The result: a triage assistant that works even without internet (SpecialistAgent + RAGAgent both run locally), with GPT as a fallback when available.

## Results

| Model | Accuracy |
|---|---|
| SpecialistAgent (fine-tuned Llama) | ~89% |
| RAGAgent (guidelines + GPT) | ~85% |
| FrontierAgent (GPT-4.1-mini zero-shot) | ~72% |
| EnsembleAgent (weighted vote) | ~91% |

## Structure

```
stella-oiro/
  agents/
    base_agent.py         — shared logging/colour base class
    specialist_agent.py   — calls Modal-deployed fine-tuned Llama
    rag_agent.py          — ChromaDB retrieval + GPT classification
    frontier_agent.py     — GPT-4.1-mini zero-shot
    ensemble_agent.py     — weighted vote across all three
    messenger_agent.py    — Pushover push notifications
    autonomous_agent.py   — tool-calling orchestrator
  modal_triage_service.py — Modal deployment for fine-tuned model
  clinical_triage_multiagent.ipynb — main notebook
```

## Setup

### 1. Prerequisites

- Fine-tuned model on HuggingFace Hub (from Week 7) — set `HF_MODEL_NAME` in the notebook
- Clinical knowledge base from Week 5 (or regenerate using the RAG notebook)

### 2. Install dependencies

```bash
uv sync
```

### 3. Set up `.env`

```
OPENAI_API_KEY=sk-...
HF_TOKEN=hf_...
PUSHOVER_USER=u...      # from pushover.net (optional)
PUSHOVER_TOKEN=a...     # from pushover.net (optional)
```

### 4. Set up Modal

```bash
uv run modal token set --token-id ak-... --token-secret as-...
```

In the Modal dashboard, add a secret named `huggingface-secret` with key `HF_TOKEN`.

### 5. Deploy the triage service

```bash
uv run modal deploy modal_triage_service.py
```

### 6. Run the notebook

Open `clinical_triage_multiagent.ipynb` and run all cells.

## Live Demo

[https://huggingface.co/spaces/AcharO/stella-oiro](https://huggingface.co/spaces/AcharO/stella-oiro)
