# Tech Doc Cheatsheet

## Problem

When learning new technologies such as Tailwind CSS, Zustand, etc., we are often overwhelmed by long technical documentations and countless reference links.  
It is hard to know where to start, and even after learning, key concepts are easily forgotten.

## Solution

This tool provides:
- A **concise cheat sheet** that summarizes core concepts from **multiple relevant documentation links**.
- **Minimal sample code** for quick understanding and reference.

By reducing reading cost and focusing on essentials, it helps users learn faster and review more efficiently.

---

## Features

- Automatically selects **beginner-relevant links** from official documentation
- Aggregates content from multiple pages into **one structured cheatsheet**
- Outputs **clean Markdown**, suitable for reading, saving, or further editing
- Designed to work both in **Jupyter Notebook** and **command-line environments**

---

## Requirements

- Python **3.10+**
- An **OpenAI API key**

---

## Installation

This project uses **uv** for fast and reproducible dependency management.

### 1. Install uv

```bash
pip install uv
```

### 2. Clone the repository

```bash
git clone <your-repo-url>
cd tech-doc-cheatsheet
```
### 3. Create a virtual environment

```bash
uv venv
```

### 4. Install dependencies

```bash
uv add openai python-dotenv
```

---

## Environment Setup

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

---

## Usage

### Run from command line

```bash
uv run python tech_doc_cheatsheet.py
```
The generated cheatsheet will be printed as Markdown.

---

## Project Structure

```text
tech-doc-cheatsheet/
├─ .env
├─ main.py
├─ scraper_modified.py
└─ README.md
```

---

## Notes

* The output length is automatically truncated to avoid exceeding model limits.
* The quality of the cheatsheet depends on the structure of the original documentation.
* This tool is intended for **learning and summarization**, not as a replacement for full documentation.

---