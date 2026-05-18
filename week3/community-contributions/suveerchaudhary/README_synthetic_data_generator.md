# Synthetic Data Generator (Week 3)

Main notebook: [`week3_synthetic_data_generator.ipynb`](week3_synthetic_data_generator.ipynb)

## Open in Google Colab

After pushing to your fork on branch `suveerchaudhary/week3-solution`:

https://colab.research.google.com/github/suveerchaudhary/llm_engineering/blob/suveerchaudhary/week3-solution/week3/community-contributions/suveerchaudhary/week3_synthetic_data_generator.ipynb

## Run in Cursor (or VS Code)

Open the same `.ipynb` in the editor, choose a **Jupyter kernel** (Python environment with dependencies installed), run cells from the top. Use a **`.env`** file for API keys (see notebook section 2). Gradio opens on **localhost** when not on Colab; use the URL printed after `launch()`.

## Colab secrets

Create secrets (key icon) matching names used in the notebook: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `HF_TOKEN`, optional `GRADIO_USER` / `GRADIO_PASS`, optional `GRADIO_SHARE` or `SYNTHGEN_GRADIO_SHARE` (`true` / `1` / `yes`) to force a public Gradio link on any runtime.

## Docs

- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- [TODO.md](TODO.md)
