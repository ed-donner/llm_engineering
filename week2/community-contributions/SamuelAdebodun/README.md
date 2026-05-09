# Technical Q&A (Week 2)

Web app that streams answers from **OpenAI (gpt-4o-mini)** or **Anthropic (Claude)**. Users pick a model in a dropdown, type a question, and see streamed Markdown in the UI. Built with Gradio; run cells in order and use the share link to open the app.

**Requirements:** `.env` with `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`.

---

## Improvements over Week 1

| Week 1 | Week 2 |
|--------|--------|
| Notebook-only: run cells, hardcoded or `input()` question | **Gradio UI**: type any question, choose model, get streamed answer in the browser |
| Two separate flows (OpenAI cell, Ollama cell) | **Single flow**: one `answer()` + `MODEL_CHOICES`; switch provider via dropdown |
| OpenAI + Ollama (local) | **OpenAI + Anthropic** (both cloud; Anthropic via OpenAI-compatible API) |
| `update_display()` in Jupyter | **Streaming to Gradio** `gr.Markdown` with copy button |
| One question per run | **Reusable app**: submit many questions without re-running cells |
