# Job one-pager – Gradio UI (Week 2)

Week 2 community contribution: **Job posting → one-pager** with a Gradio UI, model switch (OpenRouter), and streaming.

Builds on the [job-posting-one-pager](../../../community-contributions/job-posting-one-pager) (week 1 style). Adds:

- **Gradio UI** – text input, model dropdown, streaming output
- **Model switch** – pick an OpenRouter model (GPT-4o Mini, Claude, Gemini, Llama, etc.)
- **Streaming** – one-pager appears token-by-token
- **Save as .md** – write the last one-pager to `job_one_pager.md`

## Setup

From repo root, dependencies are in the main `pyproject.toml`. Ensure:

- `OPENROUTER_API_KEY` in `.env` (repo root or this folder)
- `gradio`, `openai`, `beautifulsoup4`, `requests`, `python-dotenv` (all in main project)

## Run

**Notebook:** Open `job_one_pager_gradio.ipynb` and run all cells. The app opens in your browser (paste works there).

**CLI:** `python app.py` from this folder (opens in browser).

Ensure `OPENROUTER_API_KEY` is set in `.env` (repo root or this folder).

## Deploy on Hugging Face Spaces

1. Push this folder to a new Space (SDK or git): choose **Gradio** as the SDK, set **App file** to `app.py`.
2. In the Space → **Settings** → **Repository secrets**, add a secret named `OPENROUTER_API_KEY` with your key.
3. The Space will install deps from `requirements.txt` and run `app.py`. Your one-pager app will be live.  
   (On Spaces, "Save as .md" may not write to disk; use the textbox’s copy button instead.)

## Usage

1. Paste a **job URL** (company careers page) or the **full job description** (e.g. copied from LinkedIn).
2. Choose a **model** from the dropdown (OpenRouter).
3. Click **Generate one-pager** – output streams into the textbox.
4. Click **Save as .md** to write the result to `job_one_pager.md` in this folder.

## Week 2 skills used

- **Day 1:** Multiple models via OpenRouter (model dropdown).
- **Day 2:** Gradio UI (Blocks, Textbox, Dropdown, Button, streaming).
- **Day 3:** Single-turn “assistant” pattern (system + user message).
- **Streaming:** Token-by-token output for better UX.
