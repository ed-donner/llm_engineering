# 🎙️ AI Meeting Assistant

An AI-powered meeting assistant that transcribes meeting recordings, generates concise summaries, and enables users to chat with the meeting transcript using a Large Language Model (LLM).

Built with **Streamlit**, **OpenRouter**, and speech-to-text technology.

---

## Features

- 🎧 Upload meeting recordings (`.mp3`, `.wav`, `.m4a`)
- 📝 Automatically generate a meeting summary
- 💬 Ask questions about the meeting transcript
- ⚡ Streaming responses for summaries and chat
- 📄 Context-aware conversations powered by the meeting transcript
- 🖥️ Simple and intuitive Streamlit interface

---

## Project Structure

```
.
├── app.py
├── requirements.txt
├── services/
│   ├── environment_service.py
│   ├── model_service.py
│   ├── prompt_service.py
│   └── speech_to_text_service.py
└── README.md
```

---

## Prerequisites

- Python 3.10+
- OpenRouter API Key
- Speech-to-text model/API configured in `SpeechToTextService`

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Create a virtual environment

Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root.

Example:

```env
OPENROUTER_API_KEY=your_api_key
OPENROUTER_MODEL=your_model_name
```

Depending on your implementation, additional environment variables may be required by `EnvironmentService`.

---

## Running the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

The application will be available at:

```
http://localhost:8501
```

---

## How It Works

1. Upload a meeting recording.
2. The audio is transcribed into text.
3. The transcript is used to generate a meeting summary.
4. The transcript is also injected into the LLM system prompt.
5. Users can ask questions about the meeting, and responses are generated using the transcript as context.

---

## Technologies Used

- Python
- Streamlit
- OpenRouter API
- OpenAI Python SDK
- Speech-to-Text Model/API

---

## Supported Audio Formats

- MP3
- WAV
- M4A

Maximum upload size: **100 MB**

---

## Example Workflow

1. Upload a meeting recording.
2. Wait for the transcript and summary to be generated.
3. Navigate to **Meeting Summary** to review the generated notes.
4. Navigate to **Chat with Meeting** to ask questions such as:

- What were the action items?
- Who is responsible for each task?
- What deadlines were discussed?
- Summarize the decisions made.
- Were there any blockers mentioned?

---

## Future Improvements

- Export meeting summaries as PDF or Markdown
- Download chat history
- Speaker diarization
- Multi-language transcription
- Meeting title generation
- Keyword extraction
- Action item detection
- Calendar integration

---

## License

This project is intended for educational and demonstration purposes. Modify the license section as appropriate for your use case.
