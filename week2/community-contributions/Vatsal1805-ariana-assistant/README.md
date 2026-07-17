# ARIANA - AI Research & Information Assistant

ARIANA is a multi-featured research assistant application built using Gradio. It integrates web scraping, structured data extraction, conversational memory, and dynamic tool calling (Wikipedia search, weather updates, and system time lookup).

The application supports dual backends, allowing users to switch between Google Gemini (using the cloud API) and Llama 3.2 (running locally via Ollama).

## Features

- **Webpage Summarization**: Scrapes clean text content from any user-provided URL and generates a structured, bulleted markdown summary.
- **Conversational Memory**: Maintains chat history dynamically during a multi-turn conversation.
- **Dynamic Context Injection**: Summarized webpage context is automatically injected into the system prompt, allowing the chatbot to answer questions about the loaded page.
- **Tool Calling Loop**: Automatically detects when queries need factual search, weather updates, or current time, executes the corresponding Python functions, and feeds the results back to the model.
- **JSON Facts Extraction**: Scrapes a webpage and extracts key structured data strictly as formatted JSON.

## Installation

Ensure you have Python 3.10+ installed. Install the required dependencies:

```bash
pip install gradio openai requests beautifulsoup4 python-dotenv
```

## Setup

1. Create a `.env` file in the root directory.
2. Add your Google Gemini API key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
3. (Optional) To use local model support, install Ollama and run:
   ```bash
   ollama run llama3.2
   ```

## Running the Application

Start the web interface using the following command:

```bash
python aria.py
```

Open `http://localhost:7860` in your web browser to interact with the application.
