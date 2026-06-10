# Website Summarizer

A lightweight Python-based tool to scrape and summarize the content of any website. It extracts the clean text of a web page (excluding headers, footers, styling, and scripts) and queries an LLM to generate a structured, easy-to-read summary in Markdown.

## Features

- **Boilerplate Filtering**: Strips out navigation elements, header/footer boilerplate, styles, and script tags to reduce token consumption.
- **Robust Scraping**: Uses `requests` with a custom `User-Agent` and timeout handling to bypass basic anti-scraping checks.
- **Structured Summaries**: Utilizes an LLM system prompt optimized to produce summaries structured in clean Markdown.

## Project Structure

- **[scraper.py](scraper.py)**: Contains the core logic to scrape and clean a webpage's HTML text using BeautifulSoup.
- **[main.ipynb](main.ipynb)**: Jupyter Notebook acting as the user interface, importing the scraper, asking for user input, and interacting with the LLM.
- **[requirements.txt](requirements.txt)**: List of Python packages required to run the project.

## Installation & Setup

1. **Clone or Navigate to the Directory**:
   ```bash
   cd Website_Summarizer
   ```

2. **Create a Virtual Environment** (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Notebook**:
   Start Jupyter Lab or Notebook and open `main.ipynb` to run the cells.
   ```bash
   jupyter notebook main.ipynb
   ```

## Configuration

In `main.ipynb`, the LLM connection is configured via Ollama by default:
```python
OLLAMA_BASE_URL = "http://localhost:11434/v1"
ollama = OpenAI(base_url=OLLAMA_BASE_URL, api_key='ollama')
```
Ensure your local Ollama server is running, or modify the client initialization to point to OpenAI or another provider as needed.
