# Tourist Assistant

An interactive voice-enabled tourist guide that provides information about cities, landmarks, and destinations worldwide. This application uses OpenAI's GPT models for text generation and speech features for a natural conversation experience, along with RAG capabilities and Google Places API integration for real-time attraction information.

![Tourist Assistant Screenshot](travel.jpg)

## Features

- Text-based chat interface for asking questions about tourist destinations
- Voice input capability through microphone recording
- Audio responses using OpenAI's text-to-speech technology
- Clean, responsive user interface with Gradio
- RAG (Retrieval-Augmented Generation) system using PDF knowledge base
- Google Places API integration for real-time information about attractions
- Set current location for contextual queries
- Quick access to nearby attractions information

## Requirements

- Python 3.9+
- OpenAI API key
- Google Places API key (optional, for location search features)

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project directory with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
   ```
4. (Optional) Add PDF files to the `knowledge-base/` directory to enhance the assistant's knowledge about specific locations

## Running the Application

Start the application by running:

```bash
python tourist-assistant.py
```

The interface will automatically open in your default web browser. If it doesn't, navigate to the URL shown in the terminal (typically http://127.0.0.1:7860/).

## Usage

1. Type your question about any tourist destination in the text box
2. Or click the microphone button and speak your question
3. The assistant will respond with text and spoken audio
4. Set your current location using the "Set Location" feature
5. Click "Nearby Attractions" to get information about attractions near your current location
6. Use the "Refresh Knowledge Base" button to reload PDFs in the knowledge-base directory
7. Use the "Clear" button to start a new conversation

## Technologies Used

- OpenAI GPT-4o Mini for chat completions
- OpenAI Whisper for speech-to-text
- OpenAI TTS for text-to-speech
- Langchain for RAG implementation
- FAISS for vector storage
- Google Places API for location-based attraction information
- Gradio for the web interface
- pydub for audio processing