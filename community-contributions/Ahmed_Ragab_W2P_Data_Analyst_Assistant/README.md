# Data Analyst Assistant

A mini AI assistant that demonstrates how AI can help data analysts explore data, answer questions, and create visualizations through a simple conversation.

Ask a question by typing or recording your voice. The assistant decides which tools to use, retrieves relevant data, and presents a short answer with charts when requested. This is a small learning project that brings several steps of an analyst's workflow together.

## Features

- Ask questions about marketplace products using text or voice.
- Explore prices, compare vendors, and summarize product data.
- Generate charts from query results and view them beside the answer.
- Let the model choose tools and correct tool arguments after errors, within a limited number of steps.
- Use a Gradio interface with microphone input and a plot gallery.

Example questions:

- "Which vendor sells the cheapest smart watch?"
- "Show a bar chart of the average price by product type."
- "Compare the number of products offered by each vendor."

## Tools

| Tool | Purpose |
| --- | --- |
| `transcribe` | Convert recorded speech into text using the configured Groq audio model. |
| `execute_sql_query` | Retrieve and aggregate data from the SQLite database. |
| `plot_graph` | Create bar, line, pie, scatter, or histogram charts from data. |

The orchestrator uses the OpenAI Python SDK with Groq's compatible API. It passes tool results back to the model, which uses them to decide the next step and produce an answer. Charts are saved under `assets/request_metadata/` and displayed in the app.

## Data

The demo uses **LLM-generated marketplace product data**, not real business records. It is intended for learning and demonstration.

At app startup, `assets/dbs/products.csv` is loaded into the `products` table in `assets/dbs/products.db`. The table is replaced on each startup so it reflects the CSV. The assistant uses the table schema and sample records as context for its analysis.

## Setup

1. Use Python 3.10 or newer and open a terminal in the project root.

2. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   On macOS/Linux, activate it with `source .venv/bin/activate`.

3. Install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:

   ```dotenv
   GROQ_API_KEY=your_groq_api_key
   ```

   Keep this file private. Settings load it automatically. You can also override `TEXT_TO_TEXT_LLM`, `AUDIO_TO_TEXT_LLM`, and `GROQ_BASE_URL` there; defaults are in `helpers/system_settings.py`.

5. Ensure `assets/dbs/products.csv` exists, then start the app:

   ```bash
   python main.py
   ```

6. Open the local URL printed by Gradio. Choose **Text** or **Audio**, ask a question, and select **Ask**. Allow microphone access when using voice input. An internet connection and a Groq API key with access to the configured models are required.

Linux users may need their system's PortAudio package for the local microphone helpers in `core/audio_manipulation.py`.

---

This project demonstrates AI-assisted data analysis on a small synthetic dataset. Review its answers and charts as you would any analytical result.
