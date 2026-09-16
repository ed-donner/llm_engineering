# ✈️ FlightAI — AI Airline Assistant

FlightAI is an AI-powered airline assistant built as a community contribution for **Day 4 of Ed Donner's LLM Engineering course**.

It extends the original airline assistant concept with **real flight data**, **OpenAI tool calling**, **airport name/code resolution**, and **simulated flight booking**.

## Features

* 🔎 Search real operating flights between locations
* 🛫 Accept city names, airport names, or IATA codes
* 📋 Display flight number, departure, arrival, duration, and status
* 🤖 Use OpenAI function/tool calling to decide when to search or book
* 🎫 Simulate flight bookings with a generated booking reference
* ✅ Verify that a requested flight exists on the selected route before booking
* 🛡️ Restrict the assistant to flight and airline-related queries
* 💬 Interactive Gradio chat interface

> **Note:** Bookings are simulated. No real reservation or payment is made.

## Project Structure

```text
week2-day4-airline-ai-assistant/
├── app.py
├── flight_service.py
├── airport_service.py
├── tools.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## How It Works

FlightAI follows a tool-calling workflow:

```text
User
  ↓
Gradio Chat Interface
  ↓
OpenAI Model
  ↓
Tool Call
  ├── search_flights
  │       ↓
  │   AirLabs API
  │       ↓
  │   Flight data
  │
  └── book_flight
          ↓
      Verify flight
          ↓
   Simulated booking
          ↓
      Booking result
  ↓
OpenAI response
  ↓
User
```

## Requirements

* Python 3.10+
* OpenAI API key
* AirLabs API key

## Installation

Clone the repository and move into the project directory:

```bash
git clone https://github.com/amitb-21/llm_engineering.git
cd llm_engineering/week2/community-contributions/amit-kumar-behera/week2-day4-airline-ai-assistant
```

Create and activate a virtual environment:

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
OPENAI_API_KEY=your_openai_api_key
AIRLABS_API_KEY=your_airlabs_api_key
```

Do not commit your `.env` file or API keys to Git.

## Running the Application

Start the Gradio application:

```bash
python app.py
```

The application will provide a local Gradio URL that can be opened in a browser.

## Example Queries

### Search for flights

```text
Find flights from Delhi to Mumbai
```

FlightAI will use the `search_flights` tool and retrieve flight information from AirLabs.

### Book a flight

```text
My name is Amit. Book AI2408.
```

FlightAI verifies that the requested flight exists on the selected route before creating a simulated booking.

Example response:

```text
Booking confirmed!

Passenger: Amit
Flight: AI2408
Booking reference: X7K2P9

This is a simulated booking. No real reservation or payment was made.
```

### Unsupported requests

FlightAI is intentionally restricted to airline-related tasks.

For example:

```text
Can you solve this Python problem?
```

will be politely rejected rather than answered as a general-purpose programming assistant.

## APIs and Technologies

* **OpenAI API** — LLM reasoning and tool calling
* **AirLabs API** — flight schedule data
* **Gradio** — conversational user interface
* **airportsdata** — airport and IATA code resolution
* **Python** — application logic

## Important Notes

* Flight information depends on the availability and freshness of the AirLabs API.
* The application does not make real airline reservations.
* Booking references are generated locally for demonstration purposes.
* API keys must be stored in environment variables.

## Course Connection

This project is based on the **Day 4 Airline AI Assistant** from Ed Donner's *LLM Engineering* course.

The original tool-calling concept has been extended into a standalone application with an external flight-data API and simulated booking workflow.

## Author

**Amit Kumar Behera**

Community contribution for the `llm_engineering` repository.
