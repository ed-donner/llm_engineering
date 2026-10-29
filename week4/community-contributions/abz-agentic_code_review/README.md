# Agentic Code Hardening Pipeline

A multi-step AI agent that transforms raw Python code into production-ready code — automatically adding docstrings, generating unit tests, and self-healing until all tests pass.

Built as a community contribution for the **LLM Engineering Course (Week 4)**.

---

## What It Does

```
Raw Python Code
      │
      ▼
① Docstring Generator   →  adds Google-style docstrings to every function & class
      │
      ▼
② Unit Test Writer      →  generates comprehensive pytest test cases
      │
      ▼
③ Self-Healing Loop     →  runs tests → fixes failures → retries (up to 3x)
      │
      ▼
Production-Ready Code ✅
```

---

## Models Used

| Step | Model | Provider |
|------|-------|----------|
| Docstring Generation | `gemini-3.1-flash-lite` | Google API |
| Unit Test Writing | `recursive/flint-v1.0:free` | OpenRouter |
| Self-Healing | `qwen2.5-coder:7b` | Ollama (local) |

---

## Project Structure

```
abz-agentic_code_review/
├── app.py                  # Gradio UI entry point
├── orchestrator.py         # Agent pipeline controller
├── agents/
│   ├── docstring_agent.py
│   ├── testgen_agent.py
│   └── selfheal_agent.py
├── prompts/
│   ├── docstring_prompt.py
│   ├── testgen_prompt.py
│   └── selfheal_prompt.py
├── utils/
│   ├── parsers.py          # Extract code from LLM responses
│   └── code_runner.py      # Run pytest in isolated tempdir
└── README.md
```

---

## Setup

**Prerequisites:** Python 3.10+, [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com/) with `qwen2.5-coder:7b` pulled locally.

```bash

# 1. Configure environment
.env
# Fill in your API keys

# 2. Pull local model
ollama pull qwen2.5-coder:7b

# 3. Run (from root project course)
uv run week4/community-contributions/abz-agentic_code_review/app.py
```

---

## Environment Variables

```env
GOOGLE_API_KEY=your_google_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

---

## Key Concepts Demonstrated

- **Multi-provider LLM calls** using a single OpenAI-compatible SDK
- **Agentic self-healing loop** with iterative error correction
- **Isolated code execution** via `tempfile.TemporaryDirectory`
- **Streaming UI updates** using Gradio generator functions
- **Prompt engineering** with system/user message separation

---

## Course Context

This project extends the Week 4 Python → C++ code generation notebook by applying the same multi-model pattern to a different domain: **code quality automation**.

Instructor suggestions implemented:
- ✅ Multiple models across different providers
- ✅ Agentic version with feedback loop
- ✅ Docstring/comment generation tool
- ✅ Unit test generation tool

---
