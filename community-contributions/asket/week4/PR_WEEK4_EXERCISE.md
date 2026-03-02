# Pull Request: Week 4 Exercise (Frank Asket)

**Follow the bootcamp guide:** [edwarddonner.com/pr/](https://edwarddonner.com/pr/) · Raise as **Draft PR** first · Tag **@ranskills** in description or first comment for review.

---

## Title (for GitHub PR)

**Convention:** `Bootcamp/[Group] ([Your Name]): Week X - Short Description`

**Use this (replace `[Group]` with your cohort name, e.g. Euclid):**

**Bootcamp/[Group] (Frank Asket): Week 4 - Mini meal / calorie planner agent with Gradio**

---

## Description

This PR adds my **Week 4 Exercise** to `community-contributions/asket/week4/`. It implements a **tool-using agent**: a mini meal and calorie planner with three tools — **calc_tdee**, **suggest_meal**, **grocery_list** — and a **Gradio** chat UI. The agent uses OpenRouter (or OpenAI) and an in-memory recipe list; users can ask for TDEE and macro targets, meal suggestions (e.g. vegetarian, ~2000 kcal/day), and a consolidated grocery list. Inspired by the [Fitness & nutrition planner](https://github.com/llm_engineering/community-contributions/tree/main/fitness-nutrition-planner-agent) community contribution.

**Author:** Frank Asket ([@frank-asket](https://github.com/frank-asket))

*Optional: add learnings, screenshots, or a short video (≤5 min) here.*

---

## What's in this submission

| Item | Description |
|------|-------------|
| **week4_EXERCISE.ipynb** | Single notebook: agent with three tools + Gradio ChatInterface. |
| **README.md** | Short run instructions and example prompt. |
| **PR_WEEK4_EXERCISE.md** | This PR description (copy-paste into GitHub). |

### Features

- **Tools:**  
  - `calc_tdee(age, weight_kg, height_cm, activity, sex)` — Mifflin–St Jeor + activity factor; returns TDEE and macro targets (JSON).  
  - `suggest_meal(calories_target, dietary_prefs)` — Filters in-memory recipes by tags (e.g. vegetarian, vegan), returns meals near the calorie target (JSON).  
  - `grocery_list(meal_names)` — Aggregates ingredients for the given meal names; returns a text list.
- **Agent loop:** Chat builds messages from Gradio history, calls the model with `tools` and `tool_choice="auto"`, and loops on `tool_calls` until the model returns a final text response.
- **Gradio:** `gr.ChatInterface(fn=chat)` with history handled for both tuple format and message-dict format (Gradio version-safe).
- **API:** OpenRouter (`OPENROUTER_API_KEY`) or fallback OpenAI; model `gpt-4o-mini`.
- **Recipes:** In-memory list of 8 meals (name, kcal, tags, ingredients); no external API required.

---

## Technical notes

- **API:** Same pattern as Week 2 & 3: `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`) in `.env`, `base_url="https://openrouter.ai/api/v1"` when using OpenRouter.
- **History:** `_history_to_messages(history)` supports both list-of-`[user, assistant]` tuples and list-of-`{role, content}` dicts so the chat works across Gradio versions.
- **Dependencies:** gradio, openai, python-dotenv (course setup). No new dependencies.

---

## Checklist

- [x] Changes are under `community-contributions/asket/week4/`.
- [ ] **Notebook outputs:** Clear outputs before merge if required by the repo.
- [x] No edits to owner/main repo files outside this folder.
- [x] Single notebook; runs locally.

---

## How to run

1. Set `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`) in `.env`.
2. From repo root, open `community-contributions/asket/week4/week4_EXERCISE.ipynb` and run all cells.
3. The last cell launches the Gradio app. In the chat, try e.g.: *"I'm 35, 70 kg, 170 cm, moderate activity. I need about 2000 kcal/day and I'm vegetarian. Suggest meals and a grocery list."* The agent will call the tools and summarize.

---

## Bootcamp PR checklist

- [ ] **Draft PR** — Create the PR as **Draft** first; only mark "Ready for review" / open when your reviewer (e.g. Ransford) instructs you to.
- [ ] **Title** — Use format: `Bootcamp/[Group] (Frank Asket): Week 4 - Mini meal / calorie planner agent with Gradio`.
- [ ] **Tag** — Mention **@ranskills** in the PR description or as the first comment so they get notified for review.
- [ ] **After review** — Once approved, you’ll be told to open the PR for Ed’s review and merge.

Thanks for reviewing.
