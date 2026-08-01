git # YouTube Summarize

Basic YouTube transcript summarizer using Ollama.

## Overview

This module fetches transcript text from a YouTube video and summarizes it using an Ollama model via the OpenAI-compatible endpoint.

## Requirements

- Python 3.11+
- `openai`
- `youtube-transcript-api`
- `tiktoken`
- `python-dotenv` (optional)
- Local Ollama server running and a pulled model such as `llama3.2`

## Usage

1. Start Ollama locally:

   ```bash
   ollama serve
   ```

2. Pull a model if needed:

   ```bash
   ollama pull llama3.2
   ```

3. Run the summarizer:

   ```bash
   python youtube_summarize.py https://www.youtube.com/watch?v=VIDEO_ID
   ```

4. Optional: set a custom Ollama endpoint:
   ```bash
   export OLLAMA_BASE_URL="http://localhost:11434/v1"
   ```
