# Ollama Chat — Help

A Streamlit web app for chatting with local LLMs through Ollama, using the OpenAI-compatible API.

---

## Overview

This app lets you:

- Chat with models running on an Ollama server
- Pick from installed models (loaded automatically)
- See timestamps and token usage per assistant reply
- Clear the conversation and optionally view raw API responses (debug mode)

---

## Prerequisites

1. **Python 3.9+** (recommended)
2. **Ollama** installed and running
   - Download: https://ollama.com
   - Default API: `http://localhost:11434`
3. **At least one model** pulled in Ollama, for example:
   ```bash
   ollama pull gemma:2b
   ```

---

## Installation

1. Open a terminal in the project folder (`ollama_chat`).
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install streamlit openai requests
   ```

---

## Running the app

```bash
streamlit run chat_app.py
```

Your browser should open to `http://localhost:8501`. If it does not, open that URL manually.

---

## Using the app

### Main chat area

- Type your message in the input at the bottom and press Enter.
- Your messages and the assistant's replies appear in the chat history.
- Each message shows a timestamp; assistant replies also show token counts when available (`in`, `out`, `total`).

### Sidebar settings

| Control | Description |
|--------|-------------|
| **Ollama Server URL** | API base URL. Default: `http://localhost:11434/v1`. Change this if Ollama runs on another machine or port. |
| **Choose a model** | Select from models reported by your Ollama server. The list is fetched when the app loads. |
| **Clear Conversation** | Removes all messages from the current session. |
| **Show raw response** | When enabled, attempts to show the raw API response JSON for debugging (see Troubleshooting). |

---

## How it works

1. The app connects to Ollama using the OpenAI Python client (`base_url` = your Ollama URL, `api_key` = `"ollama"`).
2. Available models are fetched from `{ollama_host}/api/tags`.
3. The full conversation history is sent with each new message so the model has context.
4. Conversation state is kept in memory for the session only; it is not saved to disk.

---

## Troubleshooting

### "Error" or connection failures

- Confirm Ollama is running: `ollama list` in a terminal.
- Check the **Ollama Server URL** (include `/v1` at the end, e.g. `http://localhost:11434/v1`).
- If using a remote server, ensure the host is reachable and any firewall allows port 11434.

### Model list is empty or shows only `gemma:2b`

- The app falls back to `gemma:2b` if it cannot reach Ollama.
- Pull a model: `ollama pull <model-name>`, then refresh the app (or change the URL to trigger a reload).

### Slow responses

- Larger models need more RAM/GPU and respond slower.
- First request after loading a model can be slower (model warm-up).

### Conversation lost after refresh

- Messages live in Streamlit session state only. Refreshing the page starts a new session.

### Debug mode does nothing

- The debug checkbox may not show output if the raw response variable is not in scope. Use the error message in chat or check the terminal where Streamlit is running for stack traces.

---

## Tips

- Use **Clear Conversation** when switching topics so the model is not confused by old context.
- For remote Ollama, use the machine's IP: `http://192.168.x.x:11434/v1`.
- Token counts depend on Ollama's OpenAI-compatible API returning usage metadata.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | Web UI |
| `openai` | OpenAI-compatible client for Ollama |
| `requests` | Fetch model list from Ollama |

---

## License / support

This is a local development chat tool. For Ollama issues, see https://github.com/ollama/ollama. For Streamlit, see https://docs.streamlit.io.
