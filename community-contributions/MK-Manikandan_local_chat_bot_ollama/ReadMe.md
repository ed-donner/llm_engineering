# Local Ollama Chatbot

A modular terminal-based chatbot for running local Large Language Models (LLMs) using the [Ollama](https://ollama.com/) framework.  
It includes streaming responses, session persistence, model management, and performance statistics.

## 🚀 Features

- Works on both **Windows** and **Linux/macOS**
- Automatically detects installed Ollama models
- Lets you choose which local model to run
- Stops other running Ollama models to free system resources
- Streams responses in real time
- Shows token usage and timing statistics for every response

## 🛠️ How It Works

1. The script starts by clearing the terminal and checking for a `chat_context.json` file.
2. If a previous session exists, you can choose to load it.
3. You select a model from your installed Ollama models.
4. Other active Ollama models are stopped to improve performance.
5. The chatbot enters an interactive chat loop and streams responses directly to the terminal.
6. When the program exits, the active model is stopped automatically.

## ⌨️ Commands

You can use these commands during the chat session:

- `bye` → Exit the chatbot
- `chat_context` → Show the current conversation history
- `stats` → Show session statistics like token usage, generation time, and average speed

## 💾 Context Persistence

The chatbot uses a `chat_context.json` file to save conversations between sessions.

### Features

- Automatically detects saved chat history on startup
- Lets you choose whether to resume the previous session
- Allows you to continue the same chat with a different model by saving the chat context and loading it again after selecting another model
- Asks whether to save the session before exiting
- Saves data in standard JSON format compatible with the Ollama API

## 📋 Prerequisites

- Ollama installed and running
- Python 3.x
- Ollama Python library

Install the Python library with:

```bash
pip install ollama
