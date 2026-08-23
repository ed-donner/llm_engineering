# Deal Intel — Agentic Deal-Hunting AI

## Overview
An end-to-end agentic system that scans product sources, estimates fair value using a hybrid LLM+RAG+ML stack, ranks best opportunities, and alerts you via push/SMS. Includes a Gradio UI and vector-space visualization.

## Prerequisites
- Environment and secrets:
  - `HF_TOKEN`, `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`
  - Either `OPENAI_API_KEY` or `DEEPSEEK_API_KEY`
  - For push notifications: `PUSHOVER_USER`, `PUSHOVER_TOKEN`
  - Optional Twilio SMS: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`
- Dependencies installed: `pip install -r requirements.txt`
- Modal set up: `modal setup` (or env vars) and credits available

## Steps & Acceptance Criteria

1) Environment Setup
- Install Python deps and export required secrets.
- Acceptance: `openai`, `chromadb`, and `modal` import successfully; `modal setup` completes.

2) Deploy Specialist Pricer on Modal
- Use `pricer_service2.py` and deploy the `Pricer` class with GPU and Hugging Face cache.
- Acceptance: `Pricer.price.remote("...")` returns a numeric price; `keep_warm.py` prints `"ok"` every cycle if used.

3) Build Product Vector Store (RAG)
- Populate `chromadb` persistent DB `products_vectorstore` with embeddings, documents, metadatas (including `price` and `category`).
- Acceptance: Query for 5 similars returns valid `documents` and `metadatas` with prices.

4) Train Classical ML Models and Save Artifacts
- Train Random Forest on embeddings → save `random_forest_model.pkl` at repo root.
- Train Ensemble `LinearRegression` over Specialist/Frontier/RF predictions → save `ensemble_model.pkl`.
- Acceptance: Files exist and load in `agents/random_forest_agent.py` and `agents/ensemble_agent.py`.

5) Verify Individual Agents
- SpecialistAgent → calls Modal pricer and returns float.
- FrontierAgent → performs RAG on `chromadb`, calls `OpenAI`/`DeepSeek`.
- RandomForestAgent → loads `random_forest_model.pkl`, encodes descriptions with `SentenceTransformer`.
- ScannerAgent → pulls RSS feeds and returns consistent structured outputs with clear-price deals.
- Acceptance: Each agent returns sensible outputs without exceptions.

6) Orchestration (Planning + Messaging)
- PlanningAgent coordinates scanning → ensemble pricing → selection against `DEAL_THRESHOLD`.
- MessagingAgent pushes alerts via Pushover; optionally Twilio SMS if enabled.
- Acceptance: Planner produces at least one `Opportunity` and alert sends with price/estimate/discount/URL.

7) Framework & Persistence
- DealAgentFramework initializes logging, loads `chromadb`, reads/writes `memory.json`.
- Acceptance: After a run, `memory.json` includes the new opportunity.

8) UI (Gradio)
- Use `price_is_right_final.py` for logs, embeddings 3D plot, and interactive table; `price_is_right.py` is a simpler alternative.
- Acceptance: UI loads; “Run” updates opportunities; selecting a row triggers alert.

9) Operational Readiness
- Keep-warm optional: ping `Pricer.wake_up.remote()` to avoid cold starts.
- Acceptance: End-to-end run latency is acceptable; reduced cold start when keep-warm is active.

10) Testing
- Run CI tests in `community_contributions/pricer_test/`.
- Add a smoke test for `DealAgentFramework.run()` and memory persistence.
- Acceptance: Tests pass; smoke run returns plausible prices and discounts.

## Usage

- Launch UI:
  - `python "Deal Intel/launcher.py" ui`
- Run planner one cycle:
  - `python "Deal Intel/launcher.py" run`
- Keep Modal warm (optional):
  - `python "Deal Intel/launcher.py" keepwarm`

## Required Artifacts
- `random_forest_model.pkl` — required by `agents/random_forest_agent.py`
- `ensemble_model.pkl` — required by `agents/ensemble_agent.py`