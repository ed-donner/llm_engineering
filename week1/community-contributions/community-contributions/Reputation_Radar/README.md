# 📡 ReputationRadar
> Real-time brand intelligence with human-readable insights.

ReputationRadar is a Streamlit dashboard that unifies Reddit, Twitter/X, and Trustpilot chatter, classifies sentiment with OpenAI (or VADER fallback), and delivers exportable executive summaries. It ships with modular services, caching, retry-aware scrapers, demo data, and pytest coverage—ready for production hardening or internal deployment.

---

## Table of Contents
- [Demo](#demo)
- [Feature Highlights](#feature-highlights)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Configuration & Credentials](#configuration--credentials)
- [Running Tests](#running-tests)
- [Working Without API Keys](#working-without-api-keys)
- [Exports & Deliverables](#exports--deliverables)
- [Troubleshooting](#troubleshooting)
- [Legal & Compliance](#legal--compliance)

---


## Demo

The video demo of the app can be found at:-
https://drive.google.com/file/d/1XZ09NOht1H5LCJEbOrAldny2L5SV1DeT/view?usp=sharing


## Feature Highlights
- **Adaptive Ingestion** – Toggle Reddit, Twitter/X, and Trustpilot independently; backoff, caching, and polite scraping keep providers happy.
- **Smart Sentiment** – Batch OpenAI classification with rationale-aware prompts and auto-fallback to VADER when credentials are missing.
- **Actionable Summaries** – Executive brief card (highlights, risks, tone, actions) plus refreshed PDF layout that respects margins and typography.
- **Interactive Insights** – Plotly visuals, per-source filtering, and a lean “Representative Mentions” link list to avoid content overload.
- **Export Suite** – CSV, Excel (auto-sized columns), and polished PDF snapshots for stakeholder handoffs.
- **Robust Foundation** – Structured logging, reusable UI components, pytest suites, Dockerfile, and Makefile for frictionless iteration.

---

## Architecture Overview
```
community-contributions/Reputation_Radar/
├── app.py                 # Streamlit orchestrator & layout
├── components/            # Sidebar, dashboard, summaries, loaders
├── services/              # Reddit/Twitter clients, Trustpilot scraper, LLM wrapper, utilities
├── samples/               # Demo JSON payloads (auto-loaded when credentials missing)
├── tests/                 # Pytest coverage for utilities and LLM fallback
├── assets/                # Placeholder icons/logo
├── logs/                  # Streaming log output
├── requirements.txt       # Runtime dependencies (includes PDF + Excel writers)
├── Dockerfile             # Containerised deployment recipe
└── Makefile               # Helper targets for install/run/test
```
Each service returns a normalised payload to keep the downstream sentiment pipeline deterministic. Deduplication is handled centrally via fuzzy matching, and timestamps are coerced to UTC before analysis.

---

## Quick Start
1. **Clone & enter the project directory (`community-contributions/Reputation_Radar`).**
2. **Install dependencies and launch Streamlit:**
   ```bash
   pip install -r requirements.txt && streamlit run app.py
   ```
   (Use a virtual environment if preferred.)
3. **Populate the sidebar:** add your brand name, optional filters, toggled sources, and API credentials (stored only in session state).
4. **Click “Run Analysis 🚀”** – follow the status indicators as sources load, sentiment processes, and summaries render.

### Optional Docker Run
```bash
docker build -t reputation-radar .
docker run --rm -p 8501:8501 -e OPENAI_API_KEY=your_key reputation-radar
```

---

## Configuration & Credentials
The app reads from `.env`, Streamlit secrets, or direct sidebar input. Expected variables:

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Enables OpenAI sentiment + executive summary (falls back to VADER if absent). |
| `REDDIT_CLIENT_ID` | PRAW client ID for Reddit API access. |
| `REDDIT_CLIENT_SECRET` | PRAW client secret. |
| `REDDIT_USER_AGENT` | Descriptive user agent (e.g., `ReputationRadar/1.0 by you`). |
| `TWITTER_BEARER_TOKEN` | Twitter/X v2 recent search bearer token. |

Credential validation mirrors the guidance from `week1/day1.ipynb`—mistyped OpenAI keys surface helpful warnings before analysis begins.

---

## Running Tests
```bash
pytest
```
Tests cover sentiment fallback behaviour and core sanitisation/deduplication helpers. Extend them as you add new data transforms or UI logic.

---

## Working Without API Keys
- Reddit/Twitter/Trustpilot can be toggled independently; missing credentials raise gentle warnings rather than hard failures.
- Curated fixtures in `samples/` automatically load for any disabled source, keeping charts, exports, and PDF output functional in demo mode.
- The LLM layer drops to VADER sentiment scoring and skips the executive summary when `OPENAI_API_KEY` is absent.

---

## Exports & Deliverables
- **CSV** – Clean, UTF-8 dataset for quick spreadsheet edits.
- **Excel** – Auto-sized columns, formatted timestamps, instantaneous import into stakeholder workbooks.
- **PDF** – Professionally typeset executive summary with bullet lists, consistent margins, and wrapped excerpts (thanks to ReportLab’s Platypus engine).

All exports are regenerated on demand and never persisted server-side.

---

## Troubleshooting
- **OpenAI key missing/invalid** – Watch the sidebar notices; the app falls back gracefully but no executive summary will be produced.
- **Twitter 401/403** – Confirm your bearer token scope and that the project has search access enabled.
- **Rate limiting (429)** – Built-in sleeps help, but repeated requests may require manual pauses. Try narrowing filters or reducing per-source limits.
- **Trustpilot blocks** – Respect robots.txt. If scraping is denied, switch to the official API or provide compliant CSV imports.
- **PDF text clipping** – Resolved by the new layout; if you customise templates ensure col widths/table styles remain inside page margins.

---

## Legal & Compliance
ReputationRadar surfaces public discourse for legitimate monitoring purposes. Always comply with each platform’s Terms of Service, local regulations, and privacy expectations. Avoid storing third-party data longer than necessary, and never commit API keys to version control—the app only keeps them in Streamlit session state.
