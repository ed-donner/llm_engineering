# 🧠 Agentic Voice/Text Support Chatbot

A multimodal chatbot interface with support for **text and voice input**, **multiple large language models (LLMs)**, and **context memory persistence** — all in a single Gradio-based GUI.

## 🚀 Features

- 🔄 **Multi-LLM switching**: Dynamically switch between OpenAI, Anthropic Claude, and Meta LLaMA (via Ollama)
- 🎤 **Voice input**: Use your microphone with live speech-to-text transcription
- 💬 **Contextual memory**: Maintain chat history even when switching models
- 🧪 **Prototype-ready**: Built with Gradio for rapid GUI testing and development

## 🛠️ Technologies Used

- [Gradio](https://www.gradio.app/) – GUI interface
- [OpenAI API](https://platform.openai.com/)
- [Anthropic Claude API](https://www.anthropic.com/)
- [Ollama](https://ollama.com/) – Local LLaMA inference
- [`speech_recognition`](https://pypi.org/project/SpeechRecognition/) – Voice-to-text
- `sounddevice`, `numpy` – Audio recording
- `.env` – Environment variable management

## You’ll also need:
- API keys for OpenAI and Claude
- Ollama installed locally to run LLaMA models
- A .env file with the necessary API keys
