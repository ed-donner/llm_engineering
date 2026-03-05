# Week 2 Exercise — Technical Explanation Assistant

![tech-assistant](https://private-user-images.githubusercontent.com/6010217/557550219-63c45593-1446-4292-b01f-b2c196ea3a92.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NzI1NDk0OTIsIm5iZiI6MTc3MjU0OTE5MiwicGF0aCI6Ii82MDEwMjE3LzU1NzU1MDIxOS02M2M0NTU5My0xNDQ2LTQyOTItYjAxZi1iMmMxOTZlYTNhOTIucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI2MDMwMyUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNjAzMDNUMTQ0NjMyWiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9MGNhNmI5MTQ4ZjhjMTgzN2VmZjAxOWVhY2UxZjIyNmNjOTZjMjA2NTg2YTY5OTJiMTIyYmI3OTcyZmE3Y2JhZCZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.hu4wLs0JHPVqq6cwFqIT5Qc4Jw3I2egI3BwWD9ojMZw)
![tech-assistant-recommender](https://private-user-images.githubusercontent.com/6010217/557549713-f2e53c94-4863-4c14-9be4-9458154b57c6.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NzI1NDk0OTIsIm5iZiI6MTc3MjU0OTE5MiwicGF0aCI6Ii82MDEwMjE3LzU1NzU0OTcxMy1mMmU1M2M5NC00ODYzLTRjMTQtOWJlNC05NDU4MTU0YjU3YzYucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI2MDMwMyUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNjAzMDNUMTQ0NjMyWiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9NTdiYWE0NDFkY2U3Y2M3MjUzYmM5MjA3NTdjN2FmNmEzODRhNDU2Y2IxNmYwN2ZlZTIxNWNjMTJhMDAwN2RkNiZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.nQZBchQonJEp7Y9iXMBCa_Z300OKjec9qdOuApKgKf8)

A streaming chatbot with tool-calling support. Ask technical questions or request book recommendations — the LLM can search Google Play Books on-the-fly via SerpAPI.

**Features:** multi-model support (GPT / Claude), streaming responses, OpenAI function calling, and a Gradio UI.

## Prerequisites

- Python 3.11+
- API keys for the providers you want to use

## Setup

1. **Install dependencies**

```bash
pip install openai google-search-results python-dotenv gradio ipython
```

1. **Create a `.env` file** in the repo root (or the directory you run from):

```env
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
SERP_API_KEY=...
```


| Variable            | Required             | Used for                              |
| ------------------- | -------------------- | ------------------------------------- |
| `OPENAI_API_KEY`    | Yes                  | GPT model access                      |
| `ANTHROPIC_API_KEY` | For Claude           | Claude via OpenAI-compatible endpoint |
| `GOOGLE_API_KEY`    | For Gemini           | Gemini via OpenAI-compatible endpoint |
| `SERP_API_KEY`      | For book search tool | SerpAPI Google Play Books queries     |


## Running

Open the notebook and run all cells:

```bash
jupyter notebook "week2 EXERCISE.ipynb"
```

The last cell launches a **Gradio UI** at `http://127.0.0.1:7870`.

## Using the Gradio UI

1. Type a question in the text box (or click an example).
2. Pick a model from the dropdown (**GPT** or **Claude**).
3. Click **Submit**.

**Try these prompts:**

- `Explain the Transformer architecture to a layperson` — straight technical answer.
- `What are the best books on AI and LLM engineering?` — triggers the book search tool, returns formatted results.

## Notebook Structure


| Section                  | What it does                                                  |
| ------------------------ | ------------------------------------------------------------- |
| Imports & Setup          | Load dependencies, environment variables, LLM clients         |
| Book Search with SerpAPI | `search_books()` and `format_book_results()`                  |
| Tool Definition          | `get_book_summary()` + OpenAI function-calling schema         |
| System Prompt            | Instructions for technical Q&A and book recommendations       |
| Tool Call Handling       | Registry + `handle_tool_calls()`                              |
| Streaming + Gradio UI    | `_stream_response()` generator, model wrappers, Gradio launch |


## Experimenting

- **Add a model**: create a new client with `OpenAI(api_key=..., base_url=...)`, add a wrapper function, and extend the Gradio dropdown.
- **Add a tool**: define a handler function, add a JSON schema to `tools`, and register it in `TOOL_REGISTRY`.
- **Adjust the system prompt**: edit `SYSTEM_PROMPT` to change the assistant's personality or expertise.

