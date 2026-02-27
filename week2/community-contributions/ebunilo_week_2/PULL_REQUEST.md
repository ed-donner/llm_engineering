# Pull Request: ebunilo_week_2 – FlightAI Assistant with Amadeus Integration

## Summary

This PR adds a Week 2 community contribution: **FlightAI Assistant**, a business application of the Airline AI Assistant (week2/day4) that retrieves real-time flight and booking data via the **Amadeus API**. The assistant uses OpenAI for chat, Gradio for the UI, and Amadeus REST APIs for flight search, inspiration, cheapest dates, and booking lookup. Credentials are managed via a `.env` file.

## What's included

### Notebook

- **`WEEK2_Exercise.ipynb`** – FlightAI Assistant with:
  - **search_flights** – Flight offers between two airports on a date
  - **flight_inspiration** – Cheapest destinations from an origin (IATA code)
  - **flight_cheapest_dates** – Cheapest travel dates for a route
  - **get_flight_order** – Retrieve a booking by order ID

### Configuration & docs

- **`.env.example`** – Template for `OPENAI_API_KEY`, `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET`
- **`README.md`** – Setup, usage, example prompts, and technical notes

## Why it's useful

- **Day 4 business application** – Implements the “interact with booking APIs” idea from week2/day4 (tools + Gradio chat).
- **Real Amadeus integration** – Live flight data instead of mock prices; uses Amadeus test environment.
- **Requests-based** – Calls Amadeus REST APIs via `requests` (avoids SDK NetworkError in some environments). OAuth2 tokens are cached.
- **Reusable pattern** – Clear separation of init, tools, chat logic, and launch for easy adaptation.

## How to run

1. Copy `.env.example` to `.env` and set:
   - `OPENAI_API_KEY` (OpenAI)
   - `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET` ([Amadeus for Developers](https://developers.amadeus.com/my-apps/) – test app)
2. Install: `pip install openai gradio python-dotenv requests`
3. Open `WEEK2_Exercise.ipynb` and run all cells.
4. The last cell launches the Gradio chat at `http://127.0.0.1:7860`.

Example prompts: *“What flights from Madrid to London on 2026-03-12?”*, *“Cheapest destinations from Paris?”*.

## Checklist

- [x] FlightAI Assistant notebook with Amadeus tools (search, inspiration, dates, order lookup)
- [x] `.env.example` with required variables
- [x] `README.md` with setup and usage

## Author

ebunilo – Week 2 community contribution (LLM Engineering course).
