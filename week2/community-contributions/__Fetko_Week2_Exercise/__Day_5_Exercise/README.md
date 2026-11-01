# AI Chef Assistant

An AI-powered recipe assistant built with Python, Gradio, OpenAI APIs, and SQLite as part of an LLM Engineering course project.

## Features

- Conversational recipe recommendations based on available ingredients and preferences.
- Ingredient lookup and nutritional calculations using a local SQLite database.
- AI-generated recipe images.
- Voice input with speech-to-text transcription.
- Text-to-speech playback of recipe instructions.
- Interactive Gradio interface with chat, recipe images, and audio controls.

## How It Works

1. The user enters a request through text or voice.
2. The assistant uses an OpenAI language model to understand the request.
3. The model can call functions to search the ingredient database and calculate nutritional values.
4. The assistant generates a recipe with ingredients and cooking instructions.
5. An image and spoken narration are generated for the recipe.
6. The results are displayed in the Gradio interface.

## Project Components

| File | Purpose |
|---|---|
| `AiChefAssistant.ipynb` | Main notebook and Gradio interface |
| `assistant.py` | Conversation handling and AI tool-calling logic |
| `tools.py` | Ingredient search and nutritional calculations |
| `database.py` | SQLite database operations |
| `seed.py` | Initial ingredient database population |
| `images.py` | AI recipe image generation |
| `audio.py` | Speech recognition and text-to-speech |

## Getting Started

1. Install Python and the project dependencies.
2. Configure your OpenAI API key in the environment.
3. Open `AiChefAssistant.ipynb` in Jupyter or VS Code.
4. Run the notebook cells in order to initialize the database and launch Gradio.
5. Open the local Gradio interface in your browser.

## Technology Stack

Python, Jupyter Notebook, Gradio, OpenAI API, SQLite.

## Notes

- OpenAI API usage may incur costs.
- The ingredient database is local and can be extended.
- Nutritional calculations depend on the accuracy of the ingredient data.
- The application is intended as an educational project.