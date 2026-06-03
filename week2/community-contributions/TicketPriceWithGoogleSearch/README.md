# Flight Ticket Price Agent

This project implements a conversational AI agent that can find and analyze flight ticket prices. Users can ask for flight prices between two cities in a natural language chat interface, and the agent will use a combination of web search and language models to provide a summary of the costs.

## Features

- **Conversational Interface:** A user-friendly chat interface built with Gradio.
- **Multi-Model Support:** Can be configured to use different Large Language Models (LLMs) for analysis, including:
  - OpenAI (e.g., GPT-4o-mini)
  - Google Gemini (e.g., Gemini 2.5 Flash)
  - Ollama (e.g., Llama 3.1)
- **Tool-Based Architecture:** The agent uses a `get_ticket_price` tool to understand when the user is asking for flight information.
- **Web Scraping & Analysis:**
  - Uses Google Custom Search to find relevant web pages with flight information.
  - Scrapes the content of the search results.
  - Leverages an LLM to analyze the scraped text and extract the lowest, highest, and average prices for one-way and round-trip flights.
- **Caching:** Caches search results to provide faster responses for repeated queries.
- **Currency Conversion:** Includes a basic currency conversion table to standardize prices to INR.

## Requirements

The project is built with Python and requires the following libraries:

- `python-dotenv`
- `openai`
- `google-generativeai`
- `ollama`
- `gradio`
- `requests`
- `beautifulsoup4`
- `google-api-python-client`
- `ipython`

You can install these dependencies using pip:
```bash
pip install python-dotenv openai google-generativeai ollama gradio requests beautifulsoup4 google-api-python-client ipython
```

## Setup

1.  **Clone the repository (optional):**
    ```bash
    git clone <repository_url>
    cd <repository_directory>/ticket_price_agent
    ```

2.  **Create a `.env` file:**
    Create a file named `.env` in the `ticket_price_agent` directory and add your API keys:
    ```env
    OPENAI_API_KEY="your_openai_api_key"
    GEMINI_API_KEY="your_gemini_api_key"
    GOOGLE_SEARCH_KEY="your_google_search_api_key"
    GOOGLE_CSE_ID="your_google_custom_search_engine_id"
    ```
    *   `GOOGLE_SEARCH_KEY` and `GOOGLE_CSE_ID` are required for the Google Custom Search API.

3.  **Install Dependencies:**
    Run the `pip install` command mentioned in the "Requirements" section.

## Usage

1.  **Open the Notebook:** Launch Jupyter Notebook or JupyterLab and open `ticket_price_agent.ipynb`.
2.  **Run the Cells:** Execute the cells in the notebook sequentially.
3.  **Interact with the Agent:** The final cell will start a Gradio chat interface. You can select the model you want to use (OpenAI or Gemini) from the dropdown menu.
4.  **Ask for Prices:** Start a conversation by asking for flight prices, for example:
    - "How much is a ticket from Delhi to Mumbai?"
    - "What's the flight cost to Kathmandu from Delhi?"

## How It Works

1.  **User Input:** The user enters a message in the Gradio chat interface.
2.  **Model Selection:** The selected LLM (OpenAI or Gemini) processes the input.
3.  **Tool Call:** The model's function-calling/tool-using capability identifies that the user is asking for a price and calls the `get_ticket_price` function with the extracted departure and destination cities.
4.  **Google Search:** The `get_ticket_price` function constructs a search query and uses the Google Custom Search API to find relevant links.
5.  **Web Scraping:** The agent scrapes the content from the top search result pages.
6.  **Price Analysis:** The scraped content is passed to another LLM instance with a specific prompt to analyze the text and extract price information (lowest, highest, average).
7.  **Response Generation:** The final price summary is returned to the main chat model, which then formulates a user-friendly response.
