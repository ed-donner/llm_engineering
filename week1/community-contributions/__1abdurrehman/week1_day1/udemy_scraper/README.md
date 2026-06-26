# 🎓 Udemy Course Analyzer

> Scrape any Udemy course curriculum and let a local LLM tell you if it's actually worth buying — based on your personal learning goals.

---

## 📌 Overview

Ever bought a Udemy course only to realize it was outdated, full of filler, or just not what you needed? This tool solves that.

It uses **Playwright** to scrape the full course curriculum from Udemy and feeds the data to a **local LLM running via Ollama** — which then acts as an expert professor and gives you an honest, structured review of the course before you spend a single rupee.

---

## 🚀 Features

- 🔍 **Automated Scraping** — Extracts full course curriculum, sections, and lecture details from any Udemy course page
- 🤖 **Local LLM Analysis** — No API costs, runs entirely on your machine via Ollama
- 📊 **Structured Review** — Always returns a consistent, detailed breakdown
- 🎯 **Goal-Based Evaluation** — Tell it your learning goal and it judges the course accordingly


---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| **Playwright** | Scraping Udemy course content |
| **Ollama** | Running LLM locally |
| **Mistral 7B** | Course analysis & review generation |
| **OpenAI SDK** | Communicating with Ollama's API endpoint |
| **Python** | Core language |

---

## ⚙️ How It Works

```
Udemy Course URL
       ↓
 Playwright Scraper
       ↓
 Course JSON Data
       ↓
 Local LLM via Ollama
(Mistral 7B / Llama 3.1)
       ↓
 Structured Course Review
```

---

## 📊 Sample Output

```
### 📊 Course Verdict:

### ✅ What's Good
- Covers ChromaDB and Vector Stores in depth — rare in free content
- Includes hands-on projects (RAG pipeline, multi-agent system)
- Logical progression from basics to advanced agent architecture

### ❌ What's Bad
- No coverage of LangGraph despite it being industry standard
- Week 1-2 content available free on YouTube
- Assumes prior ML knowledge but markets itself as beginner-friendly



### 💡 Who Should Buy This
- Intermediate Python developers looking to break into Agentic AI
- NOT for complete beginners — prior ML knowledge required

### 🔢 Score: 7/10
```

---

## 🔧 Requirements

- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- Mistral 7B model pulled
- Playwright installed

---

## 🖥️ Recommended Hardware

| GPU | VRAM | Recommended Model |
|-----|------|------------------|
| GTX 1660 Super | 6GB | `mistral:7b` ✅ |
| RTX 3060 | 12GB | `llama3.1:13b` ✅ |
| RTX 4060 | 8GB | `llama3.1:8b` ✅ |
| RTX 4090 | 24GB | `llama3.3:70b` 🏆 |
| CPU only | - | `mistral:7b` (slow) ⚠️ |

---



## ⚠️ Disclaimer

This tool is intended for personal use only to help evaluate courses before purchasing. Scraping Udemy may violate their Terms of Service. Use responsibly and at your own risk.

---

## 🤝 Contributing

Pull requests are welcome! If you find a bug or want to add a feature, feel free to open an issue first to discuss what you'd like to change.

---

## 📄 License

MIT License — free to use, modify, and distribute.