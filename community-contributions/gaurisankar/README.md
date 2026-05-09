# Document Q&A Agent

A local AI agent that reads documents (PDF, DOCX, TXT) and lets you ask questions about them in plain English — all running privately on your own machine.

## Prerequisites

1. **Ollama** installed and running — [ollama.com](https://ollama.com)
2. The **llama3.2** model pulled:
   ```bash
   ollama pull llama3.2
   ```
3. **uv** installed:
   ```bash
   curl -Ls https://astral.sh/uv/install.sh | sh
   ```

## How to Run

Open a terminal, navigate to this folder, and run:

```bash
uv run agent.py
```

The agent will ask you for a file path, then you can start asking questions about the document.

## Supported File Types

| Format | Extension |
|--------|-----------|
| PDF    | `.pdf`    |
| Word   | `.docx`   |
| Text   | `.txt`    |

## Project Structure

```
document_qa_agent/
├── agent.py             ← Main chat loop
├── llm.py               ← LLM communication
├── config.py            ← Model settings & system prompt
└── transcript_parser.py ← Document reading
```
