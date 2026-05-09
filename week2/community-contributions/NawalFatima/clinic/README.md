# 🏥 Clinic Appointment Booking Agent

An AI-powered voice and text clinic booking assistant built with LLMs, tool calling, and a SQLite database. Patients can book appointments, check doctor availability, and receive email confirmations — all through a conversational interface.

---

## Features

- Conversational booking flow guided by an LLM agent
- Real-time doctor and slot lookup from a SQLite database
- Automatic appointment creation and slot management
- Gmail email confirmation on successful booking
- Voice input via Whisper (speech-to-text)
- Voice output via Edge TTS (text-to-speech)
- Gradio chat interface

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | GPT-4.1 Mini via Groq |
| Speech to Text | Whisper Large V3 via Groq |
| Text to Speech | Edge TTS |
| Database | SQLite |
| Email | Gmail SMTP |
| UI | Gradio |
| Language | Python |

---

## Project Structure

```
clinic/
├── app.ipynb           # Gradio UI with voice and text input
├── agent.py            # LLM agent, tool calling, conversation logic
├── tools.py            # Tool schema definitions for the LLM
├── db_tools.py         # Database query functions
├── email_utils.py      # Email confirmation function
├── db_setup.py         # Database schema and seed data
├── clinic.db           # SQLite database (auto-generated)
├── clinic_agent.log    # Runtime logs (auto-generated)
└── .env                # API keys and credentials (not committed)
```

---

## Booking Flow

1. User describes their symptoms or specialty needed
2. Agent calls `get_specialist_info` to find matching doctors
3. Agent calls `get_availability_slots` to show open slots
4. User selects a slot and provides contact details
5. Agent calls `book_appointment` to confirm the booking
6. Agent calls `send_confirmation_email` to notify the patient

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/clinic-booking-agent
cd clinic-booking-agent
```

### 2. Install dependencies
```bash
pip install gradio openai edge-tts nest-asyncio python-dotenv
```

### 3. Create `.env` file
```
GROQ_API_KEY=your_groq_api_key
MY_EMAIL=your_gmail@gmail.com
APP_PASSWORD=your_gmail_app_password
```

> For Gmail, generate an App Password at: myaccount.google.com → Security → App Passwords

### 4. Initialize the database
```bash
python db_setup.py
```

### 5. Run the app
```bash
jupyter notebook app.ipynb
```
Or run all cells — the Gradio interface will launch automatically.

---

## Sample Doctors

| Doctor | Specialty | Availability |
|--------|-----------|--------------|
| Dr. Lim Wei | Dermatology | Monday, Wednesday |
| Dr. Aisha Rahman | Cardiology | Tuesday |
| Dr. Chen Yong | Pediatrics | Friday |
| Dr. Kavitha Menon | Orthopedics | Thursday |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key for LLM and Whisper |
| `MY_EMAIL` | Gmail address to send confirmations from |
| `APP_PASSWORD` | Gmail App Password (not your regular password) |

---

## .gitignore

```
clinic.db
__pycache__/
.env
*.log
*.pyc
```