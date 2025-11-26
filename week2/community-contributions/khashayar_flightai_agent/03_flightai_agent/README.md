# ✈️ FlightAI — Tool-Calling Airline Assistant  
### *A Mini Agentic AI Exercise using GPT-4o-mini, SQLite, and Gradio*

---

## 📘 Overview
This project demonstrates a **tool-calling AI agent** that behaves like a simple airline assistant.  
The system combines an OpenAI model (`gpt-4o-mini`) with two custom tools backed by a SQLite database:

- ✈️ **Price Lookup** — fetches the stored ticket price for a destination  
- 🔧 **Price Update** — modifies or inserts new ticket prices into the database  

The assistant interacts through a lightweight Gradio chat UI and responds with short, courteous airline-style answers.

---

## 🎯 Objective
The goal of this exercise is to:

1. Build a **minimal agent** capable of using external tools.  
2. Practice **structured function calling** with OpenAI’s API.  
3. Manage **stateful reasoning** across user messages and tool outputs.  

---

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install openai python-dotenv gradio
```

### 2. Add your API key

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=sk-...
```
The script automatically loads this file using `python-dotenv`.

## 🗂 Project Structure

## 🧩 Project Structure
```
03_flightai_agent/
├─ main.py
├─ prices.db           # auto-created SQLite database
├─ README.md
```

## 🧩 Tool Logic

The agent uses two tools:

### 1. get_ticket_price(destination_city)

Reads the ticket price from the SQLite database and returns a text message.

### 2. set_ticket_price(destination_city, new_price)

Updates (or inserts) the ticket price and returns a confirmation message.

A simple tool-calling loop handles model-initiated function calls, executes Python functions, and feeds results back into the conversation.

## 💬 Example Interaction

```txt
User: How much is a flight to London?
Assistant: A flight to London costs $799.

User: what about Berlin?
Assistant: I'm sorry, but I don't have the ticket price information for Berlin.

User: Update the flight price for Berlin to $599.
Assistant: The flight price for Berlin has been successfully updated to $599.
```

## 🧠 Insights Gained

- Function calling creates a clean interface between LLM reasoning and external operations.

- SQLite keeps the demo lightweight while still showing real-world data persistence.

- A short system prompt helps keep the agent concise and airline-appropriate.

## 🚀 Future Extensions

- Add multi-city comparisons or cheapest-route logic.

- Track additional fields: taxes, class upgrades, seat availability.

- Wrap as a FastAPI service or extend with LangChain / LiteLLM for more complex routing.

## 🏁 Author
Khashayar Bayati, Ph.D.

GitHub: github.com/Khashayarbayati1