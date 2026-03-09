# Week 8 - LLM-First Agentic Deal Orchestrator

## Goal

The goal of this submission is to build a deal-evaluation workflow where **LLMs are the main decision engine**, not just an add-on.  
Instead of using only fixed rules, the system uses LLM agents to:

- estimate fair market value from deal context and comparable items
- assign confidence and risk flags with structured outputs
- decide the final next action (`alert_user`, `watchlist`, or `skip`)

This makes the pipeline more realistic for agentic systems: evidence in, structured reasoning, explicit action out.

## What this implements

1. LLM valuation agent with strict JSON outputs (`estimated_value`, `confidence`, `rationale`, `risk_flags`)
2. LLM decision agent with strict JSON outputs (`action`, `selected_deal_id`, `rationale`)
3. `LLMFirstDealOrchestrator` class that runs the full agentic cycle
4. Explainable deal cards generated from valuation outputs
5. Feedback loop persisted to `feedback_log.json` and applied as prior context
6. Deterministic fallback path when `OPENAI_API_KEY` is not available

## Outcome

The notebook demonstrates a complete LLM-first orchestration flow that is interpretable, feedback-aware, and safe to run locally.

To run LLM orchestration cells, set `OPENAI_API_KEY` in your environment.

Main file: `week8_exercise.ipynb`
