# Synthetic Data Generator — TODO

Check boxes as you complete items. Primary work lives on branch `suveerchaudhary/week3-solution`, folder `week3/community-contributions/suveerchaudhary/`.

## Documentation

- [x] Add [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) (architecture, env vars, Colab URLs, CSV rules, CI notes)
- [x] Add [`TODO.md`](TODO.md) (this file)
- [x] Add [`README_synthetic_data_generator.md`](README_synthetic_data_generator.md) (Colab link + secrets)

## Commenting and readability (apply while building M1–M5)

Follow [`IMPLEMENTATION_PLAN.md` — Code comments and readability](IMPLEMENTATION_PLAN.md#code-comments-and-readability).

- [x] Notebook: markdown section titles + short intent lines for dense code cells
- [x] Each **function** has a brief docstring or leading comment (args, return, side effects)
- [x] Non-obvious **conditionals** and **retries** note the reason (e.g. parse failure, rate limit)
- [x] **Error handling** (`try`/`except`, early returns): comment what failed and what the user or caller should see
- [x] Any **optional `.py` module`**: N/A for v1 (notebook-only); keep proportional if you add helpers later

## Milestone M1 — Schema and CSV (notebook or minimal code)

- [x] Define field-spec input format in the main notebook (e.g. one field per line or `name: description`)
- [x] Implement validation: non-empty names, no duplicate headers, reasonable `N` bounds
- [x] Implement CSV writer helper (UTF-8, stable column order, correct quoting)
- [x] Add a tiny sanity-check cell: synthetic rows without LLM → CSV round-trip

## Milestone M2 — LLM backends

- [x] Wire environment variables / Colab secrets for `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `HF_TOKEN`
- [x] Implement `MODEL_CONFIG`-style registry (see `week2_EXERCISE.ipynb`)
- [x] OpenAI path: `chat.completions.create` with messages; prefer non-streaming or accumulate stream for JSON parse
- [x] Anthropic path: match week 2 OpenAI-compatible `base_url` pattern unless you switch to native SDK
- [x] Optional: Hugging Face local path using `Week_3_Day_4_models.ipynb` patterns (4-bit, `device_map="auto"`)
- [x] Implement prompt that returns **JSON array** of objects; implement fence-stripping and `json.loads` with retries

## Milestone M3 — Gradio UI

- [x] Build `gr.Blocks` layout: fields input, row count, backend selector, generate button
- [x] Show preview table (first ~20 rows) after generation
- [x] Add CSV **download** output (`gr.File` or equivalent)
- [x] Call `huggingface_hub.login` when using gated HF models
- [x] Call `launch(auth=(user, pass))` using secrets for Gradio login (no secrets in git)

## Milestone M4 — Colab and fork workflow

- [x] Create [`week3_synthetic_data_generator.ipynb`](week3_synthetic_data_generator.ipynb) with install cell and section structure from `IMPLEMENTATION_PLAN.md`
- [x] Test end-to-end on **Google Colab Free** for at least one API backend *(manual — run notebook on Colab with secrets)*
- [x] Optionally test `hf_local` on Colab GPU with a small quantized model *(manual)*
- [x] Add Colab open link (fork + `suveerchaudhary/week3-solution` + notebook path) in notebook header or optional `README_synthetic_data_generator.md`
- [x] Push tested commits to `https://github.com/suveerchaudhary/llm_engineering.git` on `suveerchaudhary/week3-solution` *(your git remote)*
- [x] Open PR to `ed-donner/llm_engineering` when ready *(manual)*

## Milestone M5 — CI/CD

- [x] Add workflow under `.github/workflows/` with `paths: [week3/community-contributions/suveerchaudhary/**]`
- [x] Restrict triggers to branch `suveerchaudhary/week3-solution` for `push`; `pull_request` uses path filter for any base branch
- [x] Job: install Python, install `nbformat`, validate all `.ipynb` under this folder
- [x] Optional: `python -m compileall` on `.py` files in this folder *(workflow step; runs when `.py` present)*
- [ ] Optional: `pytest` if you add `tests/` or test modules
- [x] Optional: `workflow_dispatch` only for manual notebook smoke test (document required secrets)

## Stretch (later)

- [ ] Second export format (e.g. JSONL, Parquet)
- [ ] Hugging Face Space deployment
- [ ] Streaming progress in Gradio during multi-batch generation
