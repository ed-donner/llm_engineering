# paperSuMMARiZER

###### A local Ollama-powered research paper summarizer. Paste any research paper URL and get a clean, structured Markdown summary including fields like title, authors, methodology, technologies, references, and the research gap.

---

## How It Works

1. A research paper URL is passed to [Jina AI Reader](https://jina.ai/reader/) which scrapes the full page content.
2. The content is sent to a local `llama3.2:3b` model running via Ollama.
3. The model extracts and formats the key sections into clean markdown.

---

## Installation Guide

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running locally
- [uv](https://docs.astral.sh/uv/) installed and running locally
- A [Jina AI](https://jina.ai) API key (free tier available)

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/ed-donner/llm_engineering.git
cd llm_engineering
```

### Step 2 — Configure Your API Key

Create a `.env` file in the project root:

```
JINA_API_KEY=your_jina_api_key_here
```

> **Note:** The Jina AI Reader API key is used to scrape research paper pages. You can get a free key at [https://jina.ai](https://jina.ai).

### Step 3 — Open the Project

Open the llm_engineering folder in your preferred code editor (like VS Code or Cursor).
Navigate to the paperSUMMARiZER.ipynb located at:

```
community-contribution/karam_sayed/paper-summarizer/paperSUMMARiZER.ipynb
```

Set your target paper URL in the notebook:

```python
paper_url = 'https://your-research-paper-url-here'
```

### Step 4 — Select kernel

Ensure you have installed the required dependencies using uv. Then, select your Jupyter kernel, preferably Python 3.12.x.

### Step 5 — Run all the cells

```
Run all the cells in paperSUMMARizer.ipynb
```
---
## Author
Developed by [Karam Sayed](https://github.com/Karam-999)

---
