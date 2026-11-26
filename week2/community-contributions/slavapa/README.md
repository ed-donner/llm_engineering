# slavapa — Week 2 community contributions

## Day 1 — Multi-bot conversations

`day1_multi_bot_chat.ipynb` — exercises from `week2/day1.ipynb`:

1. **2-way chat** (GPT optimist vs Claude pessimist) with debug prints of the stitched `messages` list
2. **3-way chat** (GPT + Claude + Gemini) using one system prompt + one user prompt that embeds the full transcript
3. **Bonus:** same 3-way pattern with Charlie on local Ollama (`llama3.2`)

Theme: whether AI can help teach Kabbalah (kabbalahmedia.info / michaellaitman.com).

### Setup

`.env` needs:

```
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
```

Optional Ollama bonus:

```bash
ollama pull llama3.2
```

Confirm [http://localhost:11434/](http://localhost:11434/) shows Ollama running.

Select the `.venv (Python 3.12.x)` Jupyter kernel.
