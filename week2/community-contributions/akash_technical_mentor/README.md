# OmniDev: Autonomous Polyglot Technical Mentor & Execution Workbench

## Overview
Full-featured solution to the Week 2 End-of-Week Exercise (`week2 EXERCISE.ipynb`). Upgrades the Week 1 Technical Question/Answerer into a multi-modal Gradio Blocks engineering workbench featuring real-time streaming, multi-model routing, autonomous developer tools, a live Python execution sandbox, a SQLite knowledge vault, and bidirectional voice audio.

## Key Capabilities
1. **Multi-Provider Model Switching:** Seamlessly switch between Google Gemini (`gemini-3.1-flash-lite`, `gemini-2.5-flash`), OpenRouter (`openrouter/free`), and OpenAI (`gpt-4.1-mini`).
2. **Three Autonomous Developer Tools:**
   - `execute_python_sandbox`: Runs Python code in an isolated namespace to verify outputs and algorithms before answering.
   - `save_technical_note`: Persists key architectural takeaways into a local SQLite database (`engineering_vault.db`).
   - `search_engineering_vault`: Searches saved technical notes across sessions.
3. **Interactive Code Workbench (`gr.Code`):** Shares live editor code with the assistant's system prompt and automatically extracts generated Python snippets into the workbench.
4. **Bidirectional Voice Audio:** Supports spoken microphone questions via multimodal transcription and speaks concise audio briefings using Microsoft Neural TTS (`en-US-ChristopherNeural`).
5. **Real-Time Streaming & Tool Telemetry:** Streams Markdown responses token-by-token and logs all JSON tool invocations in a dedicated telemetry tab.