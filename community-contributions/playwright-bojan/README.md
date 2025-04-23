# 🧠 Playwright-Based Web Scraper for openai.com  
### 📚 Community Contribution for Ed Donner's "LLM Engineering: Master AI" Course

> _“An extra exercise for those who enjoy web scraping...  
> In the community-contributions folder, you'll find an example Selenium solution from a student.”_

---

## 🔍 About This Project

This is a response to Ed Donner’s bonus exercise to scrape `https://openai.com`, which uses dynamic JavaScript rendering.  
A fellow student contributed a Selenium-based solution — this one goes a step further with **Playwright**.

---

## 🆚 Why Playwright Over Selenium?

| Feature              | Selenium                     | Playwright 🏆               |
|----------------------|------------------------------|-----------------------------|
| **Installation**     | More complex setup           | Minimal + faster setup      |
| **Speed**            | Slower due to architecture   | Faster execution (async)    |
| **Multi-browser**    | Requires config              | Built-in Chrome, Firefox, WebKit support |
| **Headless mode**    | Less stable                  | Super stable                |
| **Async-friendly**   | Not built-in                 | Native support via asyncio  |
| **Interaction APIs** | Limited                      | Richer simulation (mouse, scroll, etc.) |

---

## ⚙️ Features

- ✅ **Full JavaScript rendering** using Chromium
- ✅ **Human-like behavior simulation** (mouse movement, scrolling, typing)
- ✅ **Caching** with `diskcache`
- ✅ **Prometheus metrics**
- ✅ **Asynchronous scraping logic**
- ✅ **Content summarization via OpenAI GPT API**

---

## 🧠 Why not in JupyterLab?

Due to the async nature of Playwright and the use of `asyncio.run()`, running this inside Jupyter causes `RuntimeError` conflicts.

This solution was developed and tested in:

- 💻 WingIDE 10 Pro
- 🐧 Ubuntu via WSL
- 🐍 Conda environment with Anaconda Python 3.12

---

## 🚀 How to Run

1. Install dependencies:
```bash
pip install -r requirements.txt
