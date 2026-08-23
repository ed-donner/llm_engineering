# 🚀 Feature-to-Benefit Translator

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black?logo=ollama)
![Gemma](https://img.shields.io/badge/Model-gemma3%3A4b-purple)
![Week](https://img.shields.io/badge/LLM%20Engineering-Week%201%20Day%201-orange)

> An automated pipeline that scrapes any tech product page and uses a local LLM (Gemma 3:4b via Ollama) to translate dense technical jargon into 3 compelling, benefit-driven social media hooks — ready to post.

**Course:** [Mastering LLM Engineering — Ed Donner (Udemy)](https://edwarddonner.com/2024/11/13/llm-engineering-resources/)
**Author:** Gunuru Venkata Shiva Kumar · [GitHub](https://github.com/ShivaGunuru) · [LinkedIn](https://linkedin.com/in/shiva-gunuru)

---

## 📌 Table of Contents

- [What It Does](#what-it-does)
- [Business Value](#business-value)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Usage](#setup--usage)
- [Example Output](#example-output)

---

## What It Does

Pass any URL — a SaaS product page, AWS docs, API release notes — and get back 3 punchy social media hooks written for a non-technical audience, generated entirely by a local LLM. No cloud API costs. No data leaving your machine.

---

## Business Value

Tech companies constantly struggle to explain complex products in plain English. This tool demonstrates how generative AI can bridge that gap — translating feature specs into consumer-friendly copy in seconds, saving hours of B2B copywriting time.

---

## How It Works

```
URL input
   ↓
scraper.py  →  fetches page title + body text (truncated to 2,000 chars)
   ↓
System prompt  →  elite B2B copywriter persona + strict Hook 1/2/3 output format
   ↓
Gemma 3:4b (via Ollama local API, OpenAI-compatible endpoint)
   ↓
3 benefit-driven social media hooks
```

---

## Tech Stack

| Component        | Technology                                  |
|------------------|---------------------------------------------|
| LLM              | `gemma3:4b` via Ollama (local, free)        |
| API Client       | `openai` Python package → `localhost:11434` |
| Web Scraping     | `requests` + `BeautifulSoup4`               |
| Env Management   | `python-dotenv`                             |
| Interface        | Jupyter Notebook                            |
| Python           | 3.12                                        |

---

## Project Structure

```
feature-benefit-translator/
├── feature_to_benefit_translator.ipynb   ← main notebook (pipeline + prompt)
├── scraper.py                            ← web scraper (fetch content + links)
├── .env                                  ← API key if needed (gitignored)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup & Usage

### 1. Install Ollama + pull model

```bash
# Install Ollama: https://ollama.com
ollama pull gemma3:4b
ollama serve          # starts local API on localhost:11434
```

### 2. Clone & install dependencies

```bash
git clone https://github.com/ShivaGunuru/feature-benefit-translator.git
cd feature-benefit-translator

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Run the notebook

```bash
jupyter notebook feature_to_benefit_translator.ipynb
```

Call `generate_pitch(url)` with any product page URL.

### requirements.txt

```
openai
requests
beautifulsoup4
python-dotenv
jupyter
```

---

## Example Output

**Input URL:** `https://aws.amazon.com/ec2/`

```
Hook 1: Stop worrying about your computing costs! Amazon EC2 gives you
         the power to scale up or down instantly – without overspending.

Hook 2: Protect your data & applications with Amazon EC2's built-in security.
         The AWS Nitro System ensures a fortress-like environment for your
         most critical workloads.

Hook 3: Supercharge your business! From AI training to massive computing tasks,
         Amazon EC2 offers unparalleled performance and flexibility – designed
         to handle anything you throw at it.
```

---

## Key Concepts Demonstrated

- **Prompt Engineering** — strict persona + structured output format (Hook 1/2/3)
- **System vs User message separation** — clean role assignment to the model
- **Local LLM via OpenAI-compatible API** — Ollama as a drop-in for cloud APIs
- **Web scraping pipeline** — BeautifulSoup content extraction with noise removal

---

*Built as Day 1 project for Ed Donner's LLM Engineering course.*
