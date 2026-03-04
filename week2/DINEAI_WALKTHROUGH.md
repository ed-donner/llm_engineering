# DineAI — Restaurant Concierge Assistant
## Week 2 Exercise: Walkthrough & Plan

---

## The Concept

Build an AI-powered concierge named **Bella** for a restaurant called **La Maison**.
Guests chat with Bella to check table availability, make reservations, and explore
the menu — and Bella responds with voice and AI-generated dish imagery.

This mirrors the **FlightAI airline assistant** from Day 5 but applied to the
restaurant industry — a more universally relatable and extensible business domain.

---

## Side-by-Side: Airline → Restaurant

| Airline (Day 5)         | DineAI (This Exercise)                  |
|-------------------------|-----------------------------------------|
| `prices.db`             | `restaurant.db`                         |
| `get_ticket_price(city)`| `check_availability(date, time, guests)`|
| City destination lookup | Table / menu item lookup                |
| `artist(city)`          | `artist(dish_name)`                     |
| `talker(reply)`         | `talker(reply)` — concierge voice       |
| 1 tool                  | 3 tools                                 |

---

## Confirmed Stack

| Task                 | Tool                              | API Key Needed          |
|----------------------|-----------------------------------|-------------------------|
| Chat + Tool Calling  | OpenRouter — `moonshotai/kimi-k2` | `OPENROUTER_API_KEY`    |
| Image Generation     | Google Gemini 2.0 Flash / Imagen 3| `GOOGLE_API_KEY`        |
| Text-to-Speech       | `edge-tts` (Microsoft Edge TTS)   | None — completely free  |
| UI                   | Gradio Blocks                     | —                       |
| Database             | SQLite3                           | —                       |

### Why this stack?
- **OpenRouter** gives model flexibility — swap `CHAT_MODEL` in one line to switch between
  Kimi K2, Claude, Gemini, GPT-4o, or any other supported model.
- **Google Gemini** covers image generation at no cost via Google AI Studio free tier.
- **edge-tts** uses Microsoft Edge's TTS engine — zero cost, zero API key, high quality voices.

---

## Skills from Week 2 — Complete Map

| Day   | Skill Taught                                | Where It Appears in DineAI              |
|-------|---------------------------------------------|------------------------------------------|
| Day 1 | Multi-provider APIs, OpenAI-compatible URLs | `router_client` with OpenRouter base URL |
| Day 1 | Message history as list of dicts            | `messages` list construction             |
| Day 2 | Gradio `gr.Interface`, streaming            | Base UI structure                        |
| Day 3 | `gr.ChatInterface`, system prompt           | `system_message`, history conversion     |
| Day 3 | Dynamic system prompt modification          | Persona constraints in system message    |
| Day 4 | Tool calling loop                           | `while finish_reason == "tool_calls"`    |
| Day 4 | JSON tool schemas                           | 3 tool definitions                       |
| Day 4 | DALL-E style image generation               | `artist()` via Google Gemini             |
| Day 4 | Text-to-speech                              | `talker()` via edge-tts                  |
| Day 4 | `gr.Blocks()` custom layout                 | Full UI with chat + image + audio        |
| Day 5 | Full integration — all of the above         | Complete working assistant               |

---

## Database Schema

Three SQLite tables power the assistant:

### `tables` — Restaurant seating inventory
```sql
CREATE TABLE tables (
    id       INTEGER PRIMARY KEY,
    capacity INTEGER,           -- 2, 4, or 8 guests
    location TEXT               -- window | patio | interior | private
)
```

### `reservations` — Bookings made through the assistant
```sql
CREATE TABLE reservations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id   INTEGER,
    date       TEXT,            -- YYYY-MM-DD
    time       TEXT,            -- HH:MM
    party_size INTEGER,
    guest_name TEXT,
    FOREIGN KEY(table_id) REFERENCES tables(id)
)
```

### `menu` — Dishes with full detail
```sql
CREATE TABLE menu (
    id          INTEGER PRIMARY KEY,
    name        TEXT,
    category    TEXT,           -- starter | main | dessert | drink
    price       REAL,
    description TEXT,
    allergens   TEXT,           -- comma-separated: gluten, dairy, nuts, eggs...
    dietary     TEXT            -- vegetarian | vegan | gluten-free
)
```

The AI never sees this data directly — it queries it through tools at conversation time.

---

## The Three Tools

### Tool 1 — `check_availability(date, time, party_size)`
Queries `tables` excluding any already booked in `reservations` for that slot.
Returns a plain-text list of available options.

```
"Available for 2 on 2026-04-12 at 19:30:
 Table 1 (seats 2, window), Table 3 (seats 2, interior)"
```

### Tool 2 — `make_reservation(table_id, date, time, party_size, guest_name)`
Inserts a row into `reservations`. Returns a confirmation string.

```
"Confirmed for Sarah Mitchell — Table 1, April 12th at 7:30pm for 2 guests."
```

### Tool 3 — `get_menu_item(item_name)`
Uses `LIKE` query so partial names work (`"truffle"` finds `"Truffle Risotto"`).
Returns description, price, allergens, and dietary info.

**Side effect:** When this tool is called, we capture the dish name and pass it
to `artist()` to generate a dish image.

---

## The System Prompt — Bella's Persona

```
You are Bella, the AI concierge for La Maison — an upscale French-Italian restaurant.
You are warm, sophisticated, and attentive. Keep responses to 2 sentences or fewer.

You can help guests with:
- Checking table availability for a specific date, time, and party size
- Making reservations (always confirm the guest's name before booking)
- Answering questions about our menu, ingredients, allergens, and pricing

Always use your tools to look up real data — never guess prices, ingredients, or availability.
If a guest mentions a dish, look it up using get_menu_item.
```

Key design decisions:
- **"2 sentences or fewer"** — keeps responses concise and natural
- **"always confirm the guest's name"** — forces a multi-turn confirmation flow before writing to the database
- **"never guess"** — prevents hallucinated prices or allergen info

---

## The Tool Calling Loop — How It Works

```
1. Build messages: [system_message] + history + [user_message]
2. Call router_client with tools=tools
3. Check response.choices[0].finish_reason:
   - If "tool_calls":
       → parse tool name + arguments
       → call matching Python function
       → append assistant message + tool results to messages
       → call model again  ← (loops back to step 3)
   - If "stop":
       → extract final text reply
       → break loop
4. Speak reply with talker()
5. If a dish was looked up → generate image with artist()
6. Return (updated_history, audio_bytes, image)
```

---

## Image Generation — `artist(dish_name)`

Uses Google Gemini with a crafted food photography prompt:

```
"Professional food photography of {dish_name}.
Fine dining plating on white porcelain, soft studio lighting,
shallow depth of field, Michelin-star restaurant presentation."
```

**Strategy — try Gemini first, fall back to Imagen:**
1. Try `gemini-2.0-flash-exp` with `response_modalities=["TEXT", "IMAGE"]`
2. If that fails → try `imagen-3.0-generate-002`
3. If both fail → return `None` (Gradio handles None gracefully — panel stays empty)

---

## Text-to-Speech — `talker(text)`

Uses `edge-tts` — Microsoft Edge's TTS engine, accessed via a Python library.

```python
voice = "en-GB-SoniaNeural"   # Warm British voice — suits a fine dining concierge
```

Other voices to try:
- `en-US-AriaNeural` — warm American female
- `en-US-GuyNeural` — calm American male
- `en-GB-RyanNeural` — British male

Because `edge-tts` is async and Jupyter has a running event loop,
`nest_asyncio.apply()` is called at import time to allow `asyncio.run()` inside notebooks.

---

## Gradio Blocks UI Layout

```
┌──────────────────────────────────────────────────────┐
│     La Maison — AI Concierge — Bella                 │
├──────────────────────────┬───────────────────────────┤
│   Chatbot                │   Dish Image              │
│   (height=450)           │   (height=450)            │
│   type="messages"        │   appears when dish       │
│                          │   is looked up            │
├──────────────────────────┴───────────────────────────┤
│   Audio Player — autoplay=True (Bella's voice)       │
├──────────────────────────────────────────────────────┤
│   [Text input — scale=5]          [Send — scale=1]   │
└──────────────────────────────────────────────────────┘
```

### Event Chain (two-step with `.then()`)

```
Step 1: add_user_message()
    Input:  [message_box, chatbot]
    Output: [message_box (cleared), chatbot (user msg appended)]
    Effect: User sees their message instantly

         ↓ .then()

Step 2: chat()
    Input:  [chatbot]
    Output: [chatbot (Bella reply), audio_output, dish_image]
    Effect: All three outputs update simultaneously
```

Both `message_box.submit` and `send_btn.click` trigger the same chain.

---

## Sample Conversation Flow

### Reservation flow
```
User:   "Hi, do you have a table for 2 on April 12th at 7:30pm?"
        [check_availability("2026-04-12", "19:30", 2) called]
Bella:  "We have a window table and an interior table available —
         which would you prefer?"

User:   "The window table please."
Bella:  "Lovely choice! May I have your name to complete the reservation?"

User:   "Sarah Mitchell."
        [make_reservation(1, "2026-04-12", "19:30", 2, "Sarah Mitchell") called]
Bella:  "Perfect, Sarah! Table 1 by the window is reserved for you on
         April 12th at 7:30pm. We look forward to welcoming you."
```

### Menu enquiry (triggers image generation)
```
User:   "What's the Beef Wellington like?"
        [get_menu_item("Beef Wellington") called → artist() generates image]
Bella:  "Our Beef Wellington is tender beef fillet in mushroom duxelles and
         golden puff pastry, £42 — it contains gluten and dairy."
         [Dish image appears in right panel | Bella's voice plays]
```

### Allergen check
```
User:   "I'm vegetarian — what can I eat?"
Bella:  "Our vegetarian options include the Truffle Risotto, Caesar Salad,
         Burrata & Tomato, and both desserts — all clearly marked on the menu."
```

---

## Build Order (Progressive)

Build the solution in this exact order — each step verifies the previous one:

```
1. Setup + clients         → confirm both API keys load
2. Database setup          → run a test query to verify seeding
3. System message          → paste it, read it carefully
4. Tool Python functions   → test each one in isolation with print()
5. Tool JSON schemas       → print the list, check structure
6. Tool handler            → unit test with a mock tool_call
7. Basic gr.ChatInterface  → confirm model responds, history works
8. Add tools to chat       → test with "do you have a table for 2?"
9. artist()                → display(artist("Beef Wellington")) in a cell
10. talker()               → display(Audio(talker("Hello"), autoplay=True))
11. Full chat() function   → wire tools + image + voice together
12. gr.Blocks() UI         → launch the complete application
```

---

## Install Requirements

```bash
pip install openai google-genai gradio edge-tts nest-asyncio python-dotenv pillow
```

## Environment Variables (`.env`)

```
OPENROUTER_API_KEY=sk-or-...
GOOGLE_API_KEY=AIza...
```
