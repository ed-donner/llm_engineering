# Meeting Audio Summarizer

An end-to-end pipeline that turns meeting recordings into concise text summaries and spoken audio summaries. Upload an MP3, WAV, or M4A file and get AI-generated meeting notes you can read or listen to.

## Features

- **Audio Transcription** — choose between two engines:
  - *Google Gemini 2.0 Flash* via OpenRouter (cloud-based, fast)
  - *OpenAI Whisper Medium (English)* via Hugging Face (local, ~3 GB download on first run)
- **Transcript Summarization** — GPT-4o-mini extracts key discussion points, decisions, and action items with real-time streaming output.
- **Text-to-Speech** — converts the summary into a WAV audio file using OpenAI's `gpt-4o-mini-tts` model.
- **Interactive UI** — Gradio web interface with upload widget, live status indicators, and an audio player.

## Prerequisites

- Python 3.10+
- API keys for the following services:

| Variable | Purpose |
|---|---|
| `HF_TOKEN` | Hugging Face Hub authentication (required for Whisper download) |
| `OPENROUTER_API_KEY` | OpenRouter gateway for Gemini transcription and GPT-4o-mini summarization |
| `OPENAI_API_KEY` | OpenAI API for text-to-speech generation |

## Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**

   Create a `.env` file in the project root:

   ```
   HF_TOKEN=hf_...
   OPENROUTER_API_KEY=sk-or-...
   OPENAI_API_KEY=sk-...
   ```

3. **Run the notebook**

   Open `exercise.ipynb` in Jupyter or VS Code and run all cells. The Gradio UI will launch automatically in your browser.

## How It Works

1. **Upload** a meeting recording through the Gradio interface.
2. **Transcribe** — the audio is either sent to Gemini as a base64-encoded payload or processed locally by Whisper.
3. **Summarize** — the raw transcript is streamed to GPT-4o-mini with a system prompt that extracts discussion points, decisions, and action items.
4. **Listen** — click "Generate Audio Summary" to produce a spoken WAV version of the notes.

## Dependencies

| Package | Role |
|---|---|
| `gradio` | Interactive web UI |
| `openai` | OpenAI & OpenRouter API client |
| `transformers` | Local Whisper speech recognition |
| `huggingface_hub` | Model hub authentication |
| `python-dotenv` | `.env` file loading |
| `numpy` / `scipy` | Audio array manipulation and WAV I/O |
