# Airline Price Detection Bot

This is a Gradio application powered by LangChain and OpenAI that detects airline ticket prices and destinations from a given URL.

## Features
* **AI Tool Calling Agent**: Uses `gpt-4o-mini` to intelligently decide when to scrape a webpage.
* **Custom Web Scraper**: An embedded tool that extracts surrounding text near currency symbols (including $, €, £, and ₦).
* **Gradio Interface**: Provides a user-friendly chat UI for interacting with the AI agent.

## Pre-requisites
* You must have Python installed.
* You need an OpenAI API key.

## Installation 

1. Ensure the required LangChain and Gradio packages are installed (they should be already if you installed the project dependencies: `pip install -r requirements.txt`). 
2. Set your environment variables:
   ```bash
   # On Windows
   set OPENAI_API_KEY="your-api-key-here"
   
   # Or create a .env file containing:
   # OPENAI_API_KEY="your-api-key-here"
   ```

## Running the App

```shell
python app.py
```

Then visit the URL outputted in the terminal (usually `http://127.0.0.1:7860`).

Ask the bot: *"What are the prices for the destinations mentioned on [URL]?"*
