# ai-voice-claude

A voice-to-text tool that transcribes speech and pastes it wherever your cursor
is. Built to work with Claude Code (main insipiration) or any other text input.

## How it works

Hold **Ctrl + Shift** to record, release to transcribe. The transcribed text is
automatically pasted at your cursor position.

Uses [OpenAI Whisper large-v3](https://huggingface.co/openai/whisper-large-v3)
via the Hugging Face `transformers` library, running on GPU for fast
transcription.

## Requirements

- Python 3.13+
- NVIDIA GPU with CUDA 12.8 support
- [uv](https://github.com/astral-sh/uv)
- A microphone

## Installation

```bash
uv sync
```

The Whisper model (~3GB) will be downloaded automatically on first run.

## Usage

```bash
uv run main.py
```

- Hold **Ctrl + Shift** — start recording
- Release either key — stop recording and paste transcribed text
- Press **Escape** — exit the app

## Configuration

Edit `config.py` to change:

- `device` — microphone device index (run
  `python -c "import sounddevice as sd; print(sd.query_devices())"` to list
  devices)
- `model` — Whisper model variant
- `sampling_rate` — audio sample rate (default 16000Hz)
