# AI Travel Planner (Week 2 Exercise)

Simple AI Travel Planner: **Telegram bot** + **Gradio** UI, shared backend, sqlite3 persistence.

---

## In Case You Are Interested

### The problem

I wanted to solve **travel planning and booking with an AI chat assistant**: you tell the system where you’re going, for how many days, and your budget, and it gives you a structured itinerary, a budget breakdown, and short travel tips, like talking to a travel agent in a chat.

To practice Week 2 (multiple UIs, LLMs, persistence), I built that as **one** app that:

- Works as a **chat** (Telegram bot) and as a **web dashboard** (Gradio), so you can plan from your phone or from a browser.
- Uses **one shared AI backend** (no duplicated logic).
- Saves every request and response in **sqlite3** so you can review or reuse your plans later.

### The solution

1. **Single entry point for AI**  
   All travel planning lives in `planner.py`. The function `generate_travel_plan(destination, days, budget, user_id)` calls the LLM (OpenRouter) or a mock, then saves the result via `database.py`. Both Telegram and Gradio call this same function.

2. **Thin UI layers**
   - `bot.py` — Telegram only: parses messages like `Mombasa, 3 days, 1000`, calls `generate_travel_plan`, sends back the itinerary.
   - `app.py` — Gradio only: text/number inputs, same `generate_travel_plan` call, output in a text box.

3. **Persistence**  
   `database.py` uses sqlite3 and a single table `users_trips` (user_id, destination, days, budget, response, timestamp). Every plan is stored there.

4. **One launcher**  
   `main.py` can start the bot, the Gradio app, or both (e.g. Gradio in foreground, bot in a background thread).

So: **one backend (`planner` + `database`), two UIs (`bot`, `app`), one `main.py` to run them.**

### How you can run it

1. Clone the repo and go to this folder:
   ```bash
   cd week2/community-contributions/makinda/ai_travel_planner
   ```
2. Install dependencies (use the same Python you’ll run with):
   - **Recommended — uv** (much faster than pip): `uv pip install -r requirements.txt`  
     Install uv if needed: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`.
   - Or with pip: `python3 -m pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add:
   - `TELEGRAM_BOT_TOKEN` — from [@BotFather](https://t.me/BotFather) if you want the Telegram bot.
   - `OPENROUTER_API_KEY` — optional; without it you get a mock itinerary.
4. Run:
   - **Gradio only:** `python3 main.py --gradio` → open the URL in your browser.
   - **Telegram only:** `python3 main.py --bot` → talk to your bot (e.g. send `Mombasa, 3 days, 1000`).
   - **Both:** `python3 main.py` (Gradio + bot together).

### How you can do something similar on your own

- **Same pattern:** Put all “business logic” (e.g. one function that calls the LLM and saves to DB) in a single module. Import and call it from both Telegram and Gradio.
- **Telegram:** Use `python-telegram-bot`; in the message handler, parse the user’s text, call your backend function, then `await update.message.reply_text(result)`.
- **Gradio:** Use `gr.Button` + `gr.Textbox`/`gr.Number`; in the click handler, call the same backend function and return the string.
- **DB:** Use `sqlite3` in a small module (e.g. `init_db`, `save_trip`) and call it from the backend after each generation.

That way you get one source of truth for the AI and storage, and two UIs that stay simple and easy to extend.

---

## Project structure

```
ai_travel_planner/
├── main.py       # Starts bot and/or Gradio
├── bot.py        # Telegram logic (polling)
├── app.py        # Gradio interface
├── planner.py    # AI travel generation (single backend)
├── database.py   # sqlite3 (users_trips)
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. **Install dependencies** (use the same Python you'll run with)
   - **Recommended — uv** (much faster than pip) (tried the latter and I hate the experience):
     ```bash
     uv pip install -r requirements.txt
     ```
     Install uv if needed: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`.
   - Or with pip: `pip install -r requirements.txt` or `python3 -m pip install -r requirements.txt`

2. **Environment**
   - Copy `.env.example` or `.env.local`to `.env`
   - **Telegram**: set `TELEGRAM_BOT_TOKEN` (from [@BotFather](https://t.me/BotFather))
   - **AI**: set `OPENROUTER_API_KEY` for real itineraries; if missing, a mock plan is used

## Run

Use `python3` so the correct interpreter (with packages) is used:

- **Both** (Gradio + bot in background):  
  `python3 main.py`

- **Gradio only**:  
  `python3 main.py --gradio`

- **Telegram only**:  
  `python3 main.py --bot`

## Usage

- **Telegram**: send e.g. `Mombasa, 3 days, 1000`; bot replies with itinerary.
- **Gradio**: enter destination, days, budget; click "Generate plan".

All requests are stored in `travel_planner.db` (table `users_trips`).
