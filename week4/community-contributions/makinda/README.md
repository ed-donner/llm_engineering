# VRP Code-Generation Benchmark (Week 4)

Compare the **same LLM providers as Week 3** (OpenRouter, OpenAI, Ollama, Gemini) on a **Nairobi grocery delivery** vehicle routing (VRP) task: each model generates Python code that solves the instance and writes `vrp_result.json`. We execute the code in a sandbox and score cost, feasibility, runtime, stability, and token usage.

## Business scenario

- **3 depots**, **12 vehicles**, **configurable orders** (20–200).
- Each order: location (lat/lon), weight, delivery window, late penalty.
- Each vehicle: capacity, start depot, fuel cost/km, wage, overtime after 8h.
- Traffic: 1.0 off-peak, 1.4 during 7–9 and 16–19.
- **Goal:** Minimize total cost (distance×fuel + driver time + overtime + late penalties) while satisfying capacity and time windows.

## What we measure

| Metric                | Why it matters              |
| --------------------- | --------------------------- |
| Code generation speed | Business iteration velocity |
| Execution runtime     | Scalability                 |
| Feasibility rate      | Constraint awareness        |
| Total cost achieved   | Solution quality            |
| Token usage           | Cost of deployment          |
| Failure recovery      | Robustness                  |

**Scoring:** 50% cost (normalized), 20% feasibility, 15% runtime, 10% code stability, 5% token efficiency. Any hard constraint violation heavily penalizes feasibility.

## Synthetic data

Data is **generated**, not hardcoded: random lat/lon in Nairobi bounds, random weights, time windows, and penalties. You can vary order count, window tightness (loose/medium/tight), and seed to avoid memorization and force real algorithmic reasoning.

## Setup

1. From repo root or week4:
   ```bash
   cd week4/community-contributions/makinda
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env`. We use **OpenRouter** for API access (including OpenAI models): set `OPENROUTER_API_KEY`. Optional: `GOOGLE_API_KEY` for native Gemini; Ollama needs no key (run `ollama serve` and pull a model).

## Run

Open and run all cells in `notebook.ipynb`. The last cell launches the Gradio app.

- **Provider / Model:** Same list as Week 3.
- **Order count:** 20–200 (smaller = faster, cheaper).
- **Time window tightness:** loose / medium / tight.
- **Execution timeout:** 30–120 s.

Outputs: generated code, execution log, total cost, constraint violations, runtime, score, breakdown, business summary, and optional route plot.

## Project structure

```
makinda/
├── data_generator.py   # Synthetic orders, depots, vehicles (Nairobi)
├── problem_spec.py     # Prompt and contract (vrp_result.json)
├── evaluator.py        # Run generated code in sandbox, validate, cost
├── scoring.py         # Composite score (cost, feasibility, runtime, stability, tokens)
├── route_plot.py       # Optional matplotlib route visualization
├── vrp_benchmark.py    # LLM client (same providers as Week 3), run_benchmark()
├── notebook.ipynb      # Gradio UI
├── requirements.txt
├── .env.example
└── README.md
```

## Adversarial testing

To separate weak from strong models:

- **Tight time windows** (dropdown = tight).
- **Higher order count** (e.g. 100–150).
- Weak models may ignore time windows, overload vehicles, or crash; stronger ones use heuristics and handle edge cases.

## Reporting

Use **business-centric** framing, e.g.:

> “Model A reduces operational cost by 14% at 150 orders but runtime grows non-linearly, making it unsuitable for real-time dispatch.”

rather than only “Model A had better optimization.”
