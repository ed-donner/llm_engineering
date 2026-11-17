# Booking Agent (Week 2, Day 4)

A Gradio chat travel agent for a made-up airline, "AI flights". It quotes and books return flights by calling Python tools. Prices and bookings live in a small local SQLite database (`bookings.db`), so the model reads real rows and can't invent a price.

## The small database

`bookings.db` is **not** in the repo. `db.py` creates it next to itself the first time it is imported or run.

| Table | Columns | Starts with |
|---|---|---|
| `PRICES` | `CITY` (key), `PRICE` | 5 seed cities: new york 100, cairo 120, london 90, berlin 80, kuala lumpur 70 |
| `bookings` | `id`, `name`, `city`, `price`, `status`, `booked_at` | empty; each booking adds a row |

Re-running is safe. It uses `CREATE TABLE IF NOT EXISTS` and `INSERT OR IGNORE`, so nothing is duplicated or overwritten.

## Setup and run

1. Put `OPENAI_API_KEY=...` in a `.env` file (the course repo root works).
2. From this folder, create the database (optional, because step 3 also creates it):
   ```bash
   python db.py
   ```
3. Start the chat (it opens in your browser):
   ```bash
   python app.py
   ```
4. To start over with fresh prices and no bookings, delete `bookings.db` and run step 2 again.

To look inside the database: `sqlite3 bookings.db "select * from bookings;"`

## Try it

- "How much is a ticket to Cairo?" → the model calls `get_ticket_price`.
- "Book it, my name is Sara" → it confirms the price, then calls `book_ticket` and returns a `BK-<id>` reference.
- "STAFF: set the price of Paris to 170" → it calls `set_ticket_price`. Without `STAFF:` it refuses politely.

Every tool call prints a spy line in the terminal, so you can watch the model order tools.

## Files

- `db.py`: creates the tables, plus 3 plain functions: `get_ticket_price`, `set_ticket_price` (upsert), `book_ticket` (reads the price from the DB, returns a `BK-<id>` reference).
- `tools.py`: the 3 JSON tool cards (`tool_cards`) and a name-to-function dict (`tool_functions`) instead of an `if` chain.
- `prompt.py`: the system prompt (ask the name, confirm before booking, only change prices for messages starting with `STAFF:`).
- `chat.py`: `handle_tool_calls` and the `while` loop, capped at `MAX_ROUNDS = 5`.
- `app.py`: `gr.ChatInterface`.
- `config.py`: loads `.env`, picks the model, creates the OpenAI client.
