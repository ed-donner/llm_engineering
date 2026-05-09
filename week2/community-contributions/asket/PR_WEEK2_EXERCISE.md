# Pull Request: Week 2 Exercise (Frank Asket)

## Title (for GitHub PR)

**Week 2 Exercise: Technical Q&A prototype with Gradio, streaming, personas & tool (asket)**

---

## Description

This PR adds my **Week 2 Exercise** notebook to `community-contributions/asket/week2/`. It builds a full prototype of the Week 1 technical Q&A: **Gradio UI**, **streaming**, **system prompt** personas, **model switching** (OpenRouter GPT vs Ollama Llama), and a **tool** (current time).

### Author

**Frank Asket** ([@frank-asket](https://github.com/frank-asket)) – Founder & CTO building Human-Centered AI infrastructure.

---

## What's in this submission

| Item | Description |
|------|-------------|
| **week2_EXERCISE.ipynb** | Single notebook: Gradio app with model/persona dropdowns, chat, and tool demo. |
| **PR_WEEK2_EXERCISE.md** | This PR description (copy-paste into GitHub). |

### Features

- **Gradio UI:** `gr.Blocks()` with Chatbot, Model and Persona dropdowns, Send/Clear. Compatible with Gradio 6.x (no `type="messages"`, theme in `launch()`).
- **Streaming:** Ollama path streams token-by-token; GPT path yields the final answer (after optional tool use).
- **System prompt / expertise:** Three personas — *Technical tutor*, *Code reviewer*, *LLM explainer* — each with a dedicated system prompt.
- **Model switching:** *OpenRouter GPT* (openai/gpt-4o-mini via OpenRouter) or *Ollama Llama* (llama3.2:3b-instruct-q4_0).
- **Tool:** `get_current_time(timezone_name)` — e.g. ask *"What time is it?"* or *"Time in Europe/Paris?"* to see the assistant call the tool.
- **Output cleaning:** Reuses `strip_code_fence()` from Week 1 for clean markdown in the chat.

---

## Technical notes

- **API:** OpenRouter preferred (`OPENROUTER_API_KEY`, `base_url="https://openrouter.ai/api/v1"`). Falls back to `OPENAI_API_KEY` or default OpenAI client.
- **Models:** GPT via OpenRouter `openai/gpt-4o-mini` or direct OpenAI `gpt-4o-mini`; Ollama `llama3.2:3b-instruct-q4_0` when "Ollama Llama" is selected.
- **Dependencies:** gradio, openai, python-dotenv (course setup). No new dependencies beyond Week 2.

---

## Checklist

- [x] Changes are under `community-contributions/asket/week2/`.
- [ ] **Notebook outputs:** Clear outputs before merge if required by the repo.
- [x] No edits to owner/main repo files outside this folder.
- [x] Gradio 6.x compatible; single notebook, no external scripts.

---

## How to run

1. Set `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`) in `.env`.
2. For Ollama option: run `ollama serve` and `ollama pull llama3.2` (or equivalent).
3. From repo root, open `community-contributions/asket/week2/week2_EXERCISE.ipynb`, run all cells; the last cell launches the Gradio app in the browser.
4. Try "What time is it?" or "Time in Europe/Paris?" to see the tool in action.

Thanks for reviewing.
