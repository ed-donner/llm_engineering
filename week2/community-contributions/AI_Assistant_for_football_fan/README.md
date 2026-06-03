# AI Assistant for English Premier League (EPL) Fans

Educational Gradio chat app for EPL fans: standings, fixtures, player info, last match results, goalscorers, and local ticket booking (SQLite). You can type questions or use **voice input** (record → send; transcription via OpenAI Whisper). **EPL data:** [TheSportsDB](https://www.thesportsdb.com/league/4328-english-premier-league) (free API).

## Main concepts

- **Input:** text or **voice** (record in UI, then "Send voice"; requires `OPENAI_API_KEY` for Whisper).
- **Stack:** Python, Gradio, OpenAI-compatible API (OpenAI + OpenRouter), SQLite, `requests`.
- **LLM:** User chooses at runtime — **GPT** (gpt-4.1-mini) or **Claude** (anthropic/claude-3.5-sonnet).
- **Tools (function calling):** standings, team fixtures, last match result, match goalscorers, player search — all via TheSportsDB (league id 4328); plus `book_ticket` saving to local SQLite (no real ticket provider).

**Flow:** User message → orchestration builds messages and calls LLM with tools → tool calls run (API or DB) → results fed back to LLM → loop until final reply.

## Requirements

- **UV** (e.g. from repo root: `uv run jupyter notebook`).
- **Env** (`.env` in project root):
  - `OPENAI_API_KEY` — GPT
  - `OPENROUTER_API_KEY` — Claude
  - `THE_SPORTS_DB_API_KEY` — **optional**; default `123` (free). Set your own for [Premium](https://www.thesportsdb.com/pricing) (higher limits).

## EPL data (TheSportsDB)

- **Standings:** `lookuptable.php?l=4328`
- **Fixtures:** `eventsnextleague.php?id=4328`, filter by team
- **Player search:** `searchplayers.php?p=Name`
- **Last match / goalscorers:** `eventslast.php`, `lookuptimeline.php`

Free key `123` works without signup (~30 req/min). Optional Premium key in env for higher limits.

## How to run

1. Set `OPENAI_API_KEY` and `OPENROUTER_API_KEY` in `.env` (and optionally `THE_SPORTS_DB_API_KEY`).
2. Open `epl_assistant.ipynb` and run all cells (or from repo root: `uv run jupyter notebook` → open this notebook).
3. In the UI: choose **GPT** or **Claude**, type a question or use **voice** (record → **Send voice**; uses OpenAI Whisper). Tool calls appear in console as `[EPL Tool] Called: ...`.

## Booking

**Educational only:** "Book a ticket" saves a row to `epl_bookings.db` (SQLite) in the project folder. No real ticket provider. Table `bookings`: `id`, `match_description`, `user_identifier`, `booked_at` (ISO). The assistant asks for name/email before calling `book_ticket` if not provided.
