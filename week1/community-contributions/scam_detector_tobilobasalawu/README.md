# Scam Detector

A simple Python app that uses OpenAI to check if a message might be a scam.

## Setup

1. Install the required packages:

```bash
pip install openai python-dotenv
```

2. Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
```

3. Run the app:

```bash
python main.py
```

Enter the message you want to check. The app will explain if it looks like a scam and suggest what to do next.
