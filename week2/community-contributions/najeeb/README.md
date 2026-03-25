# Week 2 Exercise — AI Tutor

A Gradio chat app that answers technical questions in simple, teaching-style explanations. Built as the Week 2 prototype of the technical Q&A tool from Week 1.

## What it does

- **Chat UI**: Gradio `ChatInterface` so you can ask questions and see replies in a conversation.
- **Streaming**: Replies stream in token-by-token as they’re generated.
- **Teacher persona**: Uses a system prompt so the model acts as a “clear and patient teacher” — explains like for a smart 12-year-old, with simple language, one real-world analogy, and three bullet-point takeaways. Responses are structured as: definition → how it works → example/analogy → key takeaways (under ~400 words).
- **Backend**: Calls **OpenRouter** with `gpt-4o-mini`; API key is read from `.env` and checked for the `sk-or-v1` prefix.

## How to run

1. Put your OpenRouter API key in a `.env` file as `OPENAI_API_KEY`.
2. Open the notebook and run all cells.
3. Run the cell that calls `chat.launch()` — the app opens in the browser (e.g. http://127.0.0.1:7860).

## Files

- `week2 EXERCISE.ipynb` — Notebook that defines the prompt, chat callback, and Gradio app and launches it.
