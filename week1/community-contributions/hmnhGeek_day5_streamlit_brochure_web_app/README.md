# AI Brochure Generator

Generate professional company brochures automatically using Large Language Models (LLMs).

This application analyzes a company's website, intelligently identifies relevant pages such as About Us, Products, Services, Careers, and Contact pages, gathers information from those pages, and generates a polished brochure in Markdown and PDF formats.

Built with Python, Streamlit, OpenAI-compatible APIs, and web scraping.

---

## Features

- Generate company brochures from a website URL
- Automatically discover relevant pages on a website
- Scrape and aggregate website content
- Use an LLM to summarize and structure information
- Interactive Streamlit UI
- Download generated brochures as PDF
- Support for OpenAI-compatible APIs
- Configurable model and endpoint through environment variables

---

## Demo Workflow

1. Enter a company name
2. Enter the company website URL
3. Click **Generate Brochure**
4. The application:
   - Scrapes the landing page
   - Finds relevant company pages
   - Scrapes additional content
   - Sends the collected information to an LLM
   - Generates a professional brochure

5. View the brochure directly in the UI
6. Download the brochure as a PDF

---

## Project Structure

```text
2_brochure_generator/
│
├── app.py
│
├── services/
│   ├── environment_service.py
│   ├── model_service.py
│   └── prompt_service.py
│
├── utils/
│   └── scraper.py
│
├── .env
├── pyproject.toml
└── README.md
```

---

## Architecture

```text
User Input
     │
     ▼
Streamlit UI
     │
     ▼
Model Service
     │
     ├── Website Scraper
     │
     ├── Relevant Link Selection
     │
     └── LLM Brochure Generation
     │
     ▼
Markdown Brochure
     │
     ├── Render in UI
     │
     └── Export PDF
```

---

## Technologies Used

### Frontend

- Streamlit

### Backend

- Python

### AI

- OpenAI SDK
- OpenAI-Compatible APIs

### Data Collection

- BeautifulSoup
- Requests

### Export

- markdown-pdf

---

## Installation

### Clone Repository

```bash
git clone <repository-url>
cd 2_brochure_generator
```

### Create Virtual Environment

```bash
uv venv
```

Activate the environment:

Windows:

```bash
.venv\Scripts\activate
```

Linux / macOS:

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
uv sync
```

Or:

```bash
uv add streamlit
uv add openai
uv add python-dotenv
uv add beautifulsoup4
uv add requests
uv add markdown-pdf
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_api_key

AI_MODEL=gpt-4o-mini

BASE_URL=https://api.openai.com/v1
```

### Example Using Ollama

```env
OPENAI_API_KEY=ollama

AI_MODEL=llama3

BASE_URL=http://localhost:11434/v1
```

### Example Using OpenRouter

```env
OPENAI_API_KEY=your_openrouter_key

AI_MODEL=openai/gpt-4o-mini

BASE_URL=https://openrouter.ai/api/v1
```

---

## Running the Application

```bash
uv run streamlit run app.py
```

Once started, open:

```text
http://localhost:8501
```

---

## How It Works

### Step 1: Website Analysis

The application downloads and parses the company's landing page.

### Step 2: Relevant Link Discovery

An LLM analyzes all discovered links and selects pages likely to contain useful company information:

- About Us
- Products
- Services
- Team
- Careers
- Contact
- Company Overview

### Step 3: Content Collection

Selected pages are scraped and combined into a single context document.

### Step 4: Brochure Generation

The aggregated content is sent to an LLM along with carefully designed prompts.

The model produces a structured company brochure in Markdown format.

### Step 5: PDF Export

The generated brochure can be downloaded as a PDF directly from the UI.

---

## Example Use Cases

- Sales teams researching prospects
- Vendor onboarding
- Competitive analysis
- Startup research
- Lead qualification
- Business intelligence
- Company profiling

---

## Disclaimer

This project relies on publicly available website content and AI-generated summaries. Generated brochures should be reviewed before use in official business contexts.

---

## License

MIT License
