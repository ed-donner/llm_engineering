# Week 1 — Interactive Web App (FastAPI + React)

A full-stack web application that wraps the **Week 1** lessons into an interactive UI. Each lesson becomes a page where you can try the concepts hands-on — paste URLs, send prompts to different providers, visualize tokens, and stream brochures in real time.

**Full source code:** [github.com/ariel-ajpj/ed-donner-ai-llm-engineering-week1](https://github.com/ariel-ajpj/ed-donner-ai-llm-engineering-week1)

## Pages

| Page         | Lesson                  | What It Does                                                      |
| ------------ | ----------------------- | ----------------------------------------------------------------- |
| **Day 1**    | Website Summarizer      | Paste a URL and get a snarky summary powered by GPT               |
| **Day 2**    | Multi-Provider Chat     | Send a prompt to OpenAI, Gemini, or Ollama and compare results    |
| **Day 4**    | Tokens & Memory         | Visualize tokenization and see how chat memory works              |
| **Day 5**    | Brochure Generator      | Enter a company URL and get a streamed marketing brochure         |
| **Exercise** | Tech Q&A                | Ask a technical question to any provider with model selection     |

## How It Works

- **Backend:** FastAPI with a services layer that reuses the exact logic, system prompts, and patterns from each course notebook. All LLM providers use the OpenAI SDK (Gemini and Ollama via their OpenAI-compatible endpoints — the key Day 2 insight).
- **Frontend:** React + Vite + TailwindCSS with markdown rendering and SSE streaming support.
- **All providers are optional** — the app shows clear error messages if a key is missing.

## Quick Start

```bash
# Backend
cd be && ./setup.sh && ./run.sh

# Frontend (in another terminal)
cd fe && npm install && npm run dev
```

Then open http://localhost:5173.

See the [full README](https://github.com/ariel-ajpj/ed-donner-ai-llm-engineering-week1) for detailed setup instructions.

## Credits

Built by [Ariel Pires](https://arielpires.com.br).
