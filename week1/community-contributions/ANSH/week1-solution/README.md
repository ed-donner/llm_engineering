# 🎓 AI Tutor TUI

A sleek, terminal-based User Interface (TUI) for an AI Tutor, built with [Textual](https://textual.textualize.io/) and powered by local LLMs via [Ollama](https://ollama.com/). It is designed to help you build genuine, lasting understanding in software engineering, machine learning, data science, and other technical subjects.

## ✨ Features

- **Terminal Native**: A visually rich, responsive layout right in your terminal, featuring Markdown rendering and dynamic chat bubbles.
- **Local AI Powered**: Communicates seamlessly with a locally running Ollama model so your conversations remain completely private.
- **Context Injection**: Easily feed local code files or inline reference text directly into the chat session configuration as context for the AI.
- **Asynchronous & Non-blocking**: The UI remains fully interactive even while the LLM is generating responses.

## 🚀 Getting Started

### Prerequisites

1. **Python 3.8+**
2. **Ollama**: Make sure you have Ollama installed and running.
3. Start the Ollama server and ensure your target model is pulled:
   ```bash
   ollama serve
   ollama pull <your-model>
   ```

### Installation

1. Navigate to the project directory.
2. Install the necessary Python packages:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

Launch the application directly from your terminal:
```bash
python chat_app.py
```

## 📖 Usage

### Talking to the Tutor

Simply type your question into the bottom input bar and press **Enter**. The AI Tutor will respond directly in the chat window, formatting code blocks and markdown accordingly.

### Slash Commands

The app supports slash commands to control the session state and manage learning context:

| Command | Description |
|---|---|
| `/context <text>` | Set inline snippet text as the active session context. |
| `/context path/to/file` | Load an entire local file's content as context. |
| `/show-context` | Preview the current active context. |
| `/clear` | Wipe the chat UI and reset the entire session history/turn counter. |
| `/exit` | Quit the application. |
| `/help` | Show the in-app help message. |

### Keyboard Shortcuts

| Key Binding | Action |
|---|---|
| `Enter` | Send the message |
| `Ctrl+L` | Clear the chat and session history |
| `Ctrl+C` | Quit the application |

## 🏗️ Architecture Under the Hood

- `chat_app.py`: Acts as the frontend application. It establishes the layout, handles keyboard bindings, safely offloads the LLM generation to background threads, and mutates the Textual DOM to maintain the chat thread.
- `tutor.py`: Houses the backend `Tutor` interface, managing the system prompts, handling context, maintaining conversational history, and connecting directly with Ollama.

---
*Happy learning!*
