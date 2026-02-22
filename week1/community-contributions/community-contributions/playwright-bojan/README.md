# 🧠 Community Contribution: Async Playwright-based OpenAI Scraper

This contribution presents a fully asynchronous, headless-browser-based scraper for [https://openai.com](https://openai.com) using **Playwright** — an alternative to Selenium.

Developed by: [lakovicb](https://github.com/lakovicb)  
IDE used: WingIDE Pro (Jupyter compatibility via `nest_asyncio`)

---

## 📦 Features

- 🧭 Simulates human-like interactions (mouse movement, scrolling)
- 🧠 GPT-based analysis using OpenAI's API
- 🧪 Works inside **JupyterLab** using `nest_asyncio`
- 📊 Prometheus metrics for scraping observability
- ⚡ Smart content caching via `diskcache`

---

## 🚀 How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> Ensure [Playwright is installed & browsers are downloaded](https://playwright.dev/python/docs/intro)

```bash
playwright install
```

### 2. Set environment variables in `.env`

```env
OPENAI_API_KEY=your_openai_key
BROWSER_PATH=/usr/bin/chromium-browser
```

You can also define optional proxy/login params if needed.

---

## 📘 Notebooks Included

| Notebook | Description |
|----------|-------------|
| `Playwright_Solution_JupyterAsync.ipynb` | Executes async scraper directly inside Jupyter |
| `Playwright_Solution_Showcase_Formatted.ipynb` | Nicely formatted output for human reading |

---

## 🔁 Output Example

- GPT-generated summary
- Timeline of updates
- Entities and projects mentioned
- Structured topics & themes

✅ *Can be extended with PDF export, LangChain pipeline, or vector store ingestion.*

---

## 🙏 Thanks

Huge thanks to Ed Donner for the amazing course and challenge inspiration!
