# Vimaan Flight Booking Chatbot

Vimaan is an AI-powered flight search and booking chatbot built with OpenAI tool-calling, Gradio, and SQLite.

It can:
- search flight options by source, destination, passenger count, and travel date
- collect passenger details and book tickets
- generate and store a PNR for each booking

## Project Files

- `chatbot.ipynb` - main chatbot notebook with OpenAI + Gradio interface
- `db_setup.ipynb` - creates required SQLite tables
- `tools.py` - tool functions for flight search and booking
- `helpers.py` - parsing, formatting, and database helper methods
- `vimaan.db` - local SQLite database

## Prerequisites

- Python 3.10+ (recommended)
- Jupyter Notebook or JupyterLab
- RapidAPI key for the Booking.com flights API
- OpenAI API key

## Environment Variables

Create a `.env` file in this folder:

```env
OPENAI_API_KEY=your_openai_api_key
RAPID_API_KEY=your_rapidapi_key
```

## Installation

From this directory, install dependencies:

```bash
pip install openai python-dotenv gradio requests
```

## Setup and Run

1. Open and run all cells in `db_setup.ipynb` to initialize database tables.
2. Open and run all cells in `chatbot.ipynb`.
3. Launch the Gradio UI from the final cell:
   - `gr.ChatInterface(chat).launch()`
4. Open the local Gradio link shown in notebook output and start chatting.

## How It Works

1. User asks to search flights.
2. The assistant gathers required information:
   - source and destination (IATA codes)
   - number of adults
   - children ages (optional)
   - date of journey (`YYYY-MM-DD`)
3. The assistant calls `get_ticket_price` to fetch and parse flight options.
4. On booking confirmation, the assistant collects passenger details and calls `book_flight`.
5. Passenger and booking records are saved in SQLite, and a PNR is returned.

## Notes

- `source_city` and `destination_city` should be valid IATA airport codes (for example: `HYD`, `IXR`, `DEL`).
- The Booking.com API response format may change; if so, update parsing logic in `helpers.py`.
- This project currently supports flight search and booking only (no modify/cancel flow).
