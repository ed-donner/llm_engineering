# Indie Publisher & Funding Opportunity Matcher

**Week 8–style agentic solution for a real game-industry pain: indie devs need to find the right publisher/fund at the right time; manual tracking is painful.**

---

## Why this matters to you (indie dev)

As an indie, you’re busy building the game. You don’t have time to:

- Check every publisher’s “we’re open for submissions” page.
- Remember which funds (ID@Xbox, Epic MegaGrants, Indie Fund, etc.) fit your scope.
- Re-read submission guidelines to see if you’re a match.

**This tool:**

- Keeps a list of **publisher and funding opportunities** (Pixel Forge–style, ID@Xbox, PlayStation Partners, Humble, Indie Fund, Epic MegaGrants, Nintendo, etc.).
- **Scores each one** (0–100) for how well it fits a typical indie: solo/small team, 6–18 month scope, PC/console, indie-friendly genres.
- Surfaces the **best fits** in one table and can **alert you** (e.g. push notification) when something scores above a threshold.

So instead of manually tracking “who’s open?” and “do I qualify?”, you run a scan, see ranked opportunities, and act on the ones that matter.

---

## How to use it

- You can run the project as a standalone which in your setup process u will need to first setup a virtual env (venv) then install the packages in the requirements.txt file.
- Create the .env file in the root project.
- You can see the setup below on how it is done.

1. **Set up once** – Install deps, add `OPENROUTER_API_KEY` to `.env`.
2. **Open the app** – Run `python app.py`; the Gradio UI opens in your browser.
3. **Run a scan** – Click **“Run scan & score”**. The app loads opportunities, scores them with RAG + LLM, and adds the best new one to the table (with **Fit** 0–100 and **URL**).
4. **Use the table** – Sort by **Fit** to see the best matches. Click a row to re-send a push alert for that opportunity (if Pushover is set).
5. **Repeat when you care** – Run a scan weekly or before you’re ready to pitch; the list grows and you only see new + scored opportunities.

**Optional:** Add your own programs to `opportunities_data.json`; lower or raise the fit threshold in `config.py`.

---

## What does the Fit score (0–100) mean?

- **Fit** is how well an opportunity matches a typical indie profile: solo/small team, 6–18 month scope, PC/console, indie-friendly genres (roguelike, puzzle, narrative, tactics, etc.). It’s a weighted mix of (1) RAG over the game-publisher KB and (2) an LLM “indie fit” score.
- **Higher (e.g. 70–100)** – Strong match: criteria, scope, and accessibility line up well. Worth prioritizing.
- **Mid (e.g. 50)** – **Either** a genuine “okay” match (not clearly great or wrong), **or** we couldn’t score it properly (e.g. no RAG context, API error, or unparseable reply), so we fall back to 50. Treat 50 as “check it yourself” rather than “this is a perfect mid score.”
- **Lower (e.g. 0–40)** – Poor fit for the typical indie profile (e.g. wrong scope, platform, or genre).

---

**Everything lives in week8** – The knowledge base and vector store are included and built automatically inside this project.

This project:

- **Scans** curated publisher/funding opportunities (no manual RSS yet; you can add more sources).
- **Scores** each opportunity with:
  - **RAG** over a local **game-publisher-kb** (Pixel Forge–style criteria: genre, scope, platform). The KB is in `game-publisher-kb/` and the Chroma DB is built on first run if missing.
  - **LLM** fit for “typical indie” (solo/small team, 6–18 months, PC/console).
- **Ensemble** combines RAG + LLM into a single fit score (0–100).
- **Planning** agent picks the best new opportunity and, if above threshold, **alerts** you (Pushover).
- **Gradio UI** shows surfaced opportunities; “Run” runs one scan/score cycle; row select can re-send an alert.

## Prerequisites

- **Python 3.10+** (or use `uv`).
- **OpenRouter API key** in `.env`: `OPENROUTER_API_KEY=...`.
- **Optional:** `OPENROUTER_MODEL` (default `openai/gpt-4o-mini`).

## Setup

From the matcher directory:

```bash
pip install -r requirements.txt
```

Create a `.env` in this directory (or repo root) with at least:

```
OPENROUTER_API_KEY=sk-or-v1-...
```

## Run the UI

```bash
python app.py
```

On first run, the vector store is built from `game-publisher-kb/` (may take a minute). Then open the Gradio tab, click **Run scan & score** to run one cycle.

## Build the vector store manually (optional)

To pre-build the Chroma DB from the knowledge base without running the app:

```bash
python build_vectorstore.py
```

## Run headless (one cycle)

```bash
python publisher_framework.py
```

## Configuration

- **`config.py`**
  - All paths are local (no Week 5). `game_publisher_db` is created inside this project.
  - `FIT_THRESHOLD` (default 60): minimum fit score to send an alert.
  - `MAX_OPPORTUNITIES_PER_RUN`: how many new opportunities to score per run.
- **`game-publisher-kb/`**: markdown docs (submission, revenue, platforms, team, titles). Edit these to change RAG context.
- **`opportunities_data.json`**: curated list of opportunities. Add or edit entries; the scanner excludes URLs already in memory.

## How it fits Week 8

| Week 8 piece | Here                                                                                 |
| ------------ | ------------------------------------------------------------------------------------ |
| Scanner      | Loads `opportunities_data.json`, filters by memory (seen URLs).                      |
| Pricers      | **PublisherFitAgent** (RAG on local `game_publisher_db`) + **LLMFitAgent** (no RAG). |
| Ensemble     | Weighted combination → single fit score.                                             |
| Planning     | Scan → score → pick best → alert if above threshold.                                 |
| Memory       | `publisher_matcher_memory.json`: list of surfaced ScoredOpportunities.               |
| UI           | Gradio: table of opportunities, Run button, row select to re-alert.                  |
