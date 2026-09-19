# ✈️ FlightAI — Airline AI Assistant

A community contribution based on **Day 4 of Ed Donner's LLM Engineering course**.

FlightAI extends the original airline assistant with real flight data, OpenAI tool calling, airport resolution, and simulated booking.

## What I Added

- **Flight search** using the AirLabs API
- **Airport resolution** from city names, airport names, or IATA codes
- **OpenAI tool calling** for flight search and booking
- **Flight verification** before booking
- **Simulated bookings** with generated booking references
- **Gradio interface** for interacting with the assistant
- Domain restriction to **flight and airline-related queries**

## Key Learnings

- Implementing an **LLM tool-calling loop** where the model requests tools and the application executes them.
- Connecting an LLM application to **real external API data**.
- Designing clear tool schemas and handling tool results across multiple turns.
- Validating external data before performing downstream actions such as booking.
- Keeping an LLM application focused on a specific domain rather than behaving as a general-purpose chatbot.

## Architecture

```text
User
  ↓
Gradio
  ↓
OpenAI
  ↓
Tool Calling
  ├── search_flights → AirLabs API
  └── book_flight → Flight verification
  ↓
Assistant Response
```
