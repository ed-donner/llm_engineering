# Technical Q&A Assistant

A multi-model chatbot for answering programming questions with real-time streaming, voice interaction, and intelligent tool usage.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Gradio](https://img.shields.io/badge/Gradio-5.0+-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Overview

Built this as a hands-on project to explore multi-model integration and conversational AI. The assistant adapts its explanations based on the user's expertise level and can switch between OpenAI's GPT-4o-mini and Google's Gemini Flash models on the fly.

## Features

- **Multi-Model Support** — Choose between GPT-4o-mini, Gemini Flash, or get responses from both simultaneously
- **Adaptive Expertise Levels** — Beginner, Intermediate, or Expert explanations tailored to your background  
- **Real-time Streaming** — Watch responses generate token by token
- **Voice Interaction** — Speak questions via microphone, hear answers through text-to-speech
- **Function Calling** — Built-in tools for code explanation and documentation lookup

## Demo

The interface provides:
- Chat window with copy-to-clipboard support
- Model selection radio buttons
- Expertise level toggle
- Optional tools and audio settings
- Microphone input for voice queries

## Installation

```bash
git clone https://github.com/yourusername/technical-qa-assistant.git
cd technical-qa-assistant
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

Both keys are optional — the app works with just one provider configured.

## Usage

**Or explore the notebook:**
```bash
jupyter notebook technical_qa.ipynb
```

The app launches at `http://127.0.0.1:7860` by default.

## How It Works

### System Prompts

Each expertise level uses a different system prompt:

| Level | Behavior |
|-------|----------|
| Beginner | Simple analogies, step-by-step explanations, minimal jargon |
| Intermediate | Practical examples, assumes basic programming knowledge |
| Expert | Deep dives, performance considerations, architectural patterns |

### Tool Calling

When enabled, the assistant can invoke:
- `explain_code` — Analyzes code snippets in detail
- `lookup_documentation` — Retrieves reference material for topics

### Audio Pipeline

Voice input flows through Whisper for transcription, then the response gets synthesized using OpenAI's TTS with the Onyx voice.

## Project Structure

```
technical-qa-assistant/
├── technical_qa.ipynb          # Jupyter notebook version
├── requirements.txt            # Dependencies
└── README.md
```

## Requirements

- Python 3.11+
- OpenAI API key (for GPT-4o-mini, Whisper, TTS)
- Google API key (for gemini-2.0-flash-exp)

## Tech Stack

- **Gradio** — Web interface
- **OpenAI SDK** — GPT models, Whisper transcription, TTS
- **Google Generative AI** — Gemini integration
- **python-dotenv** — Environment management

## Contributing

Pull requests welcome. For major changes, open an issue first.

## License

MIT
