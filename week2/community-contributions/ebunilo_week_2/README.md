# FlightAI Assistant – Amadeus Integration

A conversational AI assistant for FlightAI airline that retrieves real-time flight and booking data via the Amadeus API. Built as a business application of the Airline AI Assistant (week2/day4), using OpenAI for chat and Gradio for the interface.

## Features

- **Flight search** – Search for flight offers between two airports on a given date
- **Flight inspiration** – Get cheapest destinations from an origin city
- **Cheapest dates** – Find the cheapest travel dates for a specific route
- **Booking lookup** – Retrieve flight order details by order ID

The assistant uses natural language; you can ask questions like “What flights are there from Madrid to London on March 15?” and it will call the Amadeus tools to fetch real data.

## Prerequisites

- Python 3.8+
- Jupyter or a compatible notebook environment

## Setup

### 1. Install dependencies

```bash
pip install openai gradio python-dotenv requests
```

### 2. Get API keys

- **OpenAI**: [platform.openai.com](https://platform.openai.com/api-keys)
- **Amadeus** (test): [developers.amadeus.com/my-apps](https://developers.amadeus.com/my-apps/) – create an app and use the Test environment

### 3. Configure environment variables

Copy `.env.example` to `.env` and add your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```
OPENAI_API_KEY=sk-your-openai-key
AMADEUS_CLIENT_ID=your-amadeus-api-key
AMADEUS_CLIENT_SECRET=your-amadeus-api-secret
```

The notebook loads `.env` from the current directory or the project root (`llm_engineering/`).

## Usage

1. Open `WEEK2_Exercise.ipynb`
2. Run all cells in order (Kernel → Run All, or run each cell with Shift+Enter)
3. The last cell launches the Gradio chat interface
4. Chat with the assistant at the local URL (e.g. `http://127.0.0.1:7860`)

### Example prompts

- *“What flights are there from Madrid to London on 2026-03-12?”*
- *“What are the cheapest destinations from Paris?”*
- *“When are the cheapest dates to fly from Madrid to Rome?”*
- *“What’s the status of my booking? Order ID is ABC123.”*

Use **IATA codes** (e.g. LHR, JFK, MAD, CDG) when you know them; the assistant can often infer codes from city names.

## Amadeus test environment

This project uses the Amadeus **test** environment (`test.api.amadeus.com`). Test data is cached and covers many routes, but not all. Some origins (e.g. smaller airports) may have no offers. For production, switch to the Amadeus production API and use production credentials.

## Technical notes

- Uses `requests` directly for Amadeus API calls instead of the Amadeus Python SDK (avoids SDK network issues in some environments)
- OAuth2 tokens are cached and refreshed automatically
- Tools use OpenAI function calling; the model decides when to invoke each Amadeus endpoint
