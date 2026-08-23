# Week 8 Assessment — The Price is Right Finale

This folder contains the **Week 8 assessment notebook** that launches the agentic “The Price is Right” UI. Here’s what I did and how the notebook works.

---

## What I did

- **Assessment deliverable:** Get the full agentic pipeline running with a Gradio UI: deal agent framework (scanner → ensemble → messenger), memory (deals surfaced so far), live logs, and a 5‑minute timer that re-runs the pipeline.
- **Model configuration:** Non-OpenAI LLM calls use **OpenRouter** with **Anthropic Claude Sonnet 4.6** (messaging agent and preprocessor). Scanner and frontier agents keep using OpenAI. Requires `OPENROUTER_API_KEY` and `OPENAI_API_KEY` in the environment (e.g. `.env`).
- **Push notifications:** When a deal above the threshold is found, you get a **Pushover** notification. Requires `PUSHOVER_USER` and `PUSHOVER_TOKEN` in the environment.
- **Path fix:** This notebook lives under `community_contributions/jaymineh`, which doesn’t contain `deal_agent_framework.py` or `price_is_right.py`. The first code cell finds the main **week8** folder and sets the working directory and `sys.path` so imports and `uv run` use the week8 code. You can run the notebook from repo root, from week8, or from this folder.

---

## How the notebook works

Run the cells in order. The notebook has three parts:

### 1. Setup path and working directory

- **What it does:** Locates the **week8** directory (the one that contains `deal_agent_framework.py` and `price_is_right.py`) by checking the current directory, then `week8/` under cwd, then parent, then parent’s parent.
- **Why:** So `from deal_agent_framework import DealAgentFramework` and later `!uv run price_is_right.py` run in the right place and see the right modules (`agents`, `log_utils`, etc.).
- **You’ll see:** `Working directory: ...\week8` (or your actual path). Run this cell **first**; the rest of the notebook depends on it.

### 2. Reset memory (optional)

- **What it does:** Imports `DealAgentFramework` and calls `DealAgentFramework.reset_memory()`, which truncates `memory.json` to the first two entries.
- **Why:** Gives the UI a small, known starting state for a clean demo. Skip this cell if you want to keep existing deals.
- **You’ll see:** `Memory reset.`

### 3. Launch the Gradio app

- **What it does:** Runs `!uv run price_is_right.py` in the week8 directory. That starts the Gradio app: deals table (from memory), streaming agent logs, 3D vector DB plot, and a timer that re-runs the pipeline every 5 minutes.
- **Why:** The assessment is “have the agentic UI running”; this cell is the actual launch.
- **To stop:** Interrupt the cell (e.g. Stop in Jupyter/Cursor). Closing the browser tab does not stop the server.

---

## Prerequisites

- Week 8 Days 1–4 done (Modal specialist, vector DB populated, scanner/messenger, framework).
- Environment variables set (e.g. in `.env` in repo root or week8):
  - `OPENAI_API_KEY` — scanner and frontier agents
  - `OPENROUTER_API_KEY` — messaging and preprocessor (Claude Sonnet 4.6 via OpenRouter)
  - `PUSHOVER_USER` and `PUSHOVER_TOKEN` — push notifications when a deal is found
  - `HF_TOKEN` and Modal credentials as needed for your setup
- From the **week8** directory you can run `uv run price_is_right.py` (or use this notebook to do it for you).

---

## File in this folder

| File | Purpose |
|------|--------|
| `week-8-assessment.ipynb` | Notebook that sets week8 as cwd/path, optionally resets memory, and launches the Price is Right UI. |
| `README.md` | This file: what we did and how the notebook works. |

The real app code lives in the parent **week8** folder: `deal_agent_framework.py`, `price_is_right.py`, `agents/`, `log_utils.py`, etc. This folder only contains the assessment notebook and this README.
