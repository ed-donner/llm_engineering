# Pull Request: Week 3 Exercise (Frank Asket)

## Title (for GitHub PR)

**Week 3 Exercise: Synthetic dataset generator with Gradio (asket)**

---

## Description

This PR adds my **Week 3 Exercise** notebook to `community-contributions/asket/week3/`. It implements a **synthetic dataset generator**: the user describes a business scenario (e.g. restaurant reviews, support tickets); the LLM generates structured synthetic data (CSV or JSON) via **OpenRouter** (or OpenAI). **Gradio UI** for scenario, row count, and format. Runs locally — no Colab or HuggingFace token required.

### Author

**Frank Asket** ([@frank-asket](https://github.com/frank-asket)) – Founder & CTO building Human-Centered AI infrastructure.

---

## What's in this submission

| Item | Description |
|------|-------------|
| **week3_EXERCISE.ipynb** | Single notebook: synthetic data generator + Gradio UI. |
| **PR_WEEK3_EXERCISE.md** | This PR description (copy-paste into GitHub). |

### Features

- **Scenario-driven:** User describes the dataset in natural language; the model infers a sensible schema and generates fake but realistic records.
- **Formats:** CSV or JSON output; raw text (no markdown wrappers) for easy copy or export.
- **API:** OpenRouter (`OPENROUTER_API_KEY`) or fallback OpenAI; model `gpt-4o-mini`.
- **Gradio 6.x:** Simple UI (scenario textbox, row slider 1–50, format dropdown, output textbox). Theme passed to `launch()`.
- **No PII:** Prompt instructs the model to generate only synthetic, non-identifiable data.

---

## Technical notes

- **API:** Same pattern as Week 1 & 2: `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`) in `.env`, `base_url="https://openrouter.ai/api/v1"` when using OpenRouter.
- **Dependencies:** gradio, openai, python-dotenv (course setup). No HuggingFace or Colab-specific code.

---

## Checklist

- [x] Changes are under `community-contributions/asket/week3/`.
- [ ] **Notebook outputs:** Clear outputs before merge if required by the repo.
- [x] No edits to owner/main repo files outside this folder.
- [x] Single notebook; runs locally.

---

## How to run

1. Set `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`) in `.env`.
2. From repo root, open `community-contributions/asket/week3/week3_EXERCISE.ipynb` and run all cells.
3. The last cell launches the Gradio app; enter a scenario (e.g. "product catalog with name, price, category"), choose rows and format, then click Generate.

Thanks for reviewing.
