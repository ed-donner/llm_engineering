
# Fitness & Nutrition Planner Agent (Community Contribution)

A tool-using agent that generates a **7‑day vegetarian-friendly meal plan** with **calorie/macro targets** and a **consolidated grocery list**. It supports **targeted swaps** (e.g., "swap Tuesday lunch") while honoring dietary patterns, allergies, and dislikes.

> **Disclaimer**: This project is for educational purposes and is **not** medical advice. Consult a licensed professional for medical or specialized dietary needs.

---

## ✨ Features
- Calculates **TDEE** and **macro targets** via Mifflin–St Jeor + activity factors.
- Builds a **7‑day plan** (breakfast/lunch/dinner) respecting dietary constraints.
- Produces an aggregated **grocery list** for the week.
- Supports **swap** of any single meal while keeping macros reasonable.
- Minimal **Streamlit UI** for demos.
- Extensible **tool-based architecture** to plug real recipe APIs/DBs.

---

## 🧱 Architecture
- **Agent core**: OpenAI function-calling (tools) with a simple orchestration loop.
- **Tools**:
  1. `calc_calories_and_macros` – computes targets.
  2. `compose_meal_plan` – creates the 7‑day plan.
  3. `grocery_list_from_plan` – consolidates ingredients/quantities.
  4. `swap_meal` – replaces one meal (by kcal proximity and constraints).
- **Recipe source**: a tiny in-memory recipe DB for demo; replace with a real API or your own dataset.

---

## 🚀 Quickstart

### 1) Install
```bash
pip install openai streamlit pydantic python-dotenv
```

### 2) Configure
Create a `.env` file in this folder:
```
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

### 3) Run CLI (example)
```bash
python agent.py
```

### 4) Run UI
```bash
streamlit run app.py
```

---

## 🧪 Sample Profile (from issue author)
See `sample_profile.json` for the exact values used to produce `demo_output.md`.
- **Sex**: female
- **Age**: 45
- **Height**: 152 cm (~5 ft)
- **Weight**: 62 kg
- **Activity**: light
- **Goal**: maintain
- **Diet**: vegetarian

---

## 🔧 Extend
- Replace the in-memory recipes with:
  - A real **recipe API** (e.g., Spoonacular) or
  - Your **own dataset** (CSV/DB) + filters/tags
- Add price lookups to produce a **budget-aware** grocery list.
- Add **adherence tracking** and charts.
- Integrate **wearables** or daily steps to refine TDEE dynamically.
- Add **snacks** for days slightly under target kcals.

---

## 🛡️ Safety Notes
- The agent warns for extreme deficits but does **not** diagnose conditions.
- For calorie targets below commonly recommended minimums (e.g., ~1200 kcal/day for many adults), advise consulting a professional.

---

## 📁 Project Layout
```
fitness-nutrition-planner-agent/
├─ README.md
├─ agent.py
├─ app.py
├─ sample_profile.json
└─ demo_output.md
```

---

## 🤝 How to contribute
- Keep notebooks (if any) with **cleared outputs**.
- Follow the course repo’s contribution guidelines.
- Include screenshots or a short Loom/YT demo link in your PR description.
