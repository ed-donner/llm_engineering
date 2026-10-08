# TechMentor AI — Technical Q&A Assistant

Welcome to my Week 2 Capstone exercise for the LLM Engineering course! This project is a full-featured prototype of a technical Q&A assistant built with **Gradio**.

## ✨ Features
This application includes several core and bonus features explored during Week 2:

- **Multi-Model Support**: Seamlessly switch between different model providers, including:
  - Groq OSS models (e.g., Llama 3)
  - OpenAI / OpenRouter models (e.g., GPT-4o-mini)
  - Local Ollama models
- **Real-Time Streaming**: Responses are streamed token-by-token directly into the UI for a fast, responsive user experience.
- **Custom System Prompting**: Inject a custom system prompt to control the AI's persona, expertise level, and response formatting.
- **Tool Sandbox (Bonus)**: The assistant has the ability to write and execute Python code in a safe sandbox environment to answer questions or test scripts.
- **Voice Multi-Modal (Bold Bonus)**:
  - **Speech-to-Text**: Record or upload audio questions, which are transcribed using Whisper models.
  - **Text-to-Speech**: The assistant's text responses are converted back into playable audio using `gTTS` or OpenAI TTS.

## 📁 Files Included
- `app.py`: The complete Gradio web application script. Run this file to launch the UI.
- `Chatbot.ipynb`: A Jupyter Notebook version containing interactive cells for the exercise steps, from basic API calling to system prompting and the final Gradio app code.

## 🚀 How to Run

1. Make sure you have the required dependencies installed (e.g., `gradio`, `openai`, `groq`, `gTTS`).
2. Add your API keys to a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_key
   OPENAI_API_KEY=your_key
   ```
3. Run the application from the terminal:
   ```bash
   python app.py
   ```
4. Open the provided `localhost` link in your browser to interact with the assistant!
