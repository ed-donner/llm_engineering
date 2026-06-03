
# 🧠 Community Contribution: Async Playwright-based AI Scraper

## Overview
This project is a fully asynchronous, headless-browser-based scraper built using Playwright and the OpenAI API.  
It scrapes and analyzes content from four AI-related websites, producing structured summaries in Markdown and Jupyter notebook formats.  
Playwright was chosen over Selenium for its speed and efficiency, making it ideal for modern web scraping tasks.

**Developed by:** lakovicb  
**IDE used:** WingIDE Pro 10 (Jupyter compatibility via nest_asyncio)  
**Python version:** 3.12.9 (developed and tested with Anaconda)

---

## 📦 Features
- 🧭 Simulates human-like interactions (mouse movement, scrolling)
- 🧠 GPT-based analysis using OpenAI's API
- 🧪 Works inside JupyterLab using nest_asyncio
- 📊 Prometheus metrics for scraping observability
- ⚡ Smart content caching via diskcache
- 📝 Generates structured Markdown summaries and Jupyter notebooks

---

## 🚀 How to Run

### 1. Install dependencies
Run these commands in your terminal:
```bash
conda install python-dotenv prometheus_client diskcache nbformat
pip install playwright openai
playwright install
```
> Note: Ensure your environment supports Python 3.12 for optimal performance.

---

### 2. Set environment variables
Create a `.env` file in `/home/lakov/projects/llm_engineering/` with:
```env
OPENAI_API_KEY=your_openai_key
```
(Optional) Define proxy/login parameters if needed.

---

### 3. Run the scraper
```bash
python playwright_ai_scraper.py
```
This scrapes and analyzes the following URLs:
- https://www.anthropic.com
- https://deepmind.google
- https://huggingface.co
- https://runwayml.com

---

### 4. Generate notebooks
```bash
python notebook_generator.py
```
Enter a URL when prompted to generate a Jupyter notebook in the `notebooks/` directory.

---

## 📊 Results

### Python Files for Developers
- `playwright_ai_scraper.py`: Core async scraper and analyzer.
- `notebook_generator.py`: Creates Jupyter notebooks for given URLs.

These files enable transparency, reproducibility, and extendability.

---

### Markdown Summaries
Saved in `outputs/`:
- Structured analyses with sections for Summary, Entities, Updates, Topics, and Features.
- Readable and portable format.

---

### Jupyter Notebooks
Available in `notebooks/`:
- `Playwright_AI_Scraper_JupyterAsync.ipynb`
- `Playwright_AI_Scraper_Showcase_Formatted.ipynb`

---

## 🔍 Playwright vs. Selenium

| Criteria              | Selenium                              | Playwright                           |
|------------------------|---------------------------------------|--------------------------------------|
| Release Year           | 2004                                  | 2020                                 |
| Supported Browsers     | Chrome, Firefox, Safari, Edge, IE     | Chromium, Firefox, WebKit            |
| Supported Languages    | Many                                  | Python, JS/TS, Java, C#              |
| Setup                  | Complex (WebDrivers)                  | Simple (auto-installs binaries)      |
| Execution Speed        | Slower                                | Faster (WebSocket)                   |
| Dynamic Content        | Good (requires explicit waits)        | Excellent (auto-waits)               |
| Community Support      | Large, mature                        | Growing, modern, Microsoft-backed    |

> **Playwright** was chosen for its speed, simplicity, and modern feature set.

---

## ⚙️ Asynchronous Code and WingIDE Pro 10

- Fully async scraping with `asyncio`.
- Developed using WingIDE Pro 10 for:
  - Robust async support
  - Full Python 3.12 compatibility
  - Integration with JupyterLab via `nest_asyncio`
  - Stability and efficient debugging

---

## 📁 Directory Structure

```bash
playwright_ai_scraper.py         # Main scraper script
notebook_generator.py            # Notebook generator script
outputs/                         # Markdown summaries
notebooks/                       # Generated Jupyter notebooks
requirements.txt                 # List of dependencies
scraper_cache/                   # Cache directory
```

---

## 📝 Notes

- Uses Prometheus metrics and diskcache.
- Ensure a valid OpenAI API key.
- Potential extensions: PDF export, LangChain pipeline, vector store ingestion.

- **Note:** Due to the dynamic nature and limited static text on the Huggingface.co homepage, the scraper retrieved only minimal information, which resulted in a limited AI-generated summary. This behavior reflects a realistic limitation of scraping dynamic websites without interaction-based extraction.


---

## 🙏 Thanks

Special thanks to **Ed Donner** for the amazing course and project challenge inspiration!
