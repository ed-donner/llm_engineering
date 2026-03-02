# Week 3 — profe-ssor contributions

Community contributions for Week 3 (LLM Engineering course).

---

## Project 2: Meeting Minutes + Read Summary Aloud

**Notebook:** `week3 Exercise.ipynb`

A Gradio app that turns meeting audio into written minutes and can read the summary aloud.

### What it does

- **Input:** Upload a meeting or call recording (e.g. `.mp3`, `.wav`, `.m4a`).
- **Pipeline:**
  1. **Whisper** (OpenAI) — speech-to-text transcription.
  2. **GPT** (`gpt-4o-mini`) — summarization into meeting minutes (summary, discussion points, takeaways, action items with owners).
- **Output:** Transcript + meeting minutes in markdown.
- **Read aloud:** Button **"Read summary aloud"** uses OpenAI TTS to generate and play an audio version of the minutes.

### Tech stack

- **OpenAI API:** Whisper (transcription), Chat (summarization), TTS (speech).
- **Gradio:** UI (upload, run pipeline, play TTS).
- **Python:** `openai`, `gradio`, `dotenv`; temp files for TTS MP3.

### How to run

1. Set `OPENAI_API_KEY` in `.env` (or environment).
2. Open `week3 Exercise.ipynb`, run all cells.
3. Use the Gradio UI: upload audio → get transcript + minutes → optionally click **Read summary aloud**.

**Note:** TTS requires an OpenAI account with billing enabled. If TTS is unavailable, the app shows a message and continues without audio.

---

## Synthetic Dataset Generator

**Notebook:** `synthetic_dataset_generator.ipynb`

Step-by-step notebook to generate synthetic tabular datasets with an LLM (Ollama or OpenRouter). Includes fixed schemas (e.g. product reviews, support tickets, quiz Q&A), custom schema support, and a Gradio UI to generate and download CSV.

See the notebook for full instructions.
