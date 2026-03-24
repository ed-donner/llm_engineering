# Week 1 — Community Contributions

Clean, production-ready implementations of Week 1 exercises using OpenRouter and Ollama.

## Quick Start

```bash
cd week1/community-contributions/haben
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.2
cp env.example .env
```

## Environment Setup

Create `.env` file with required variables:

```bash
# OpenRouter (for GPT models)
OPENROUTER_API_KEY=sk-or-your-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini

# Ollama (for local models)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2
```

Ensure Ollama is running: `ollama serve`

## Notebooks

### `w1d1-ollama-web-summarizer.ipynb`

Webpage summarizer using local Ollama instead of GPT.

**Features:**
- Single-URL summarization
- Streaming responses
- Configurable logging

**Usage:**
```python
display_summary("https://example.com")
```

### `w1d5-brochure-builder.ipynb`

Automated company brochure generator from website content.

**Features:**
- Intelligent link selection
- Multi-page content aggregation
- Streaming support

**Usage:**
```python
create_brochure("Company Name", "https://company.com")
create_brochure("Company Name", "https://company.com", stream=True)
```

### `w1d5-technical-explainer-comparison.ipynb`

Technical question explainer comparing GPT-4o-mini and Llama 3.2 responses.

**Features:**
- Side-by-side model comparison
- Streaming GPT responses
- Automated explanation comparison

**Usage:**
```python
# Edit question in Cell 2, then run all cells
```

## Files

- `w1d1-ollama-web-summarizer.ipynb` - Ollama-based web summarizer
- `w1d5-brochure-builder.ipynb` - Company brochure generator
- `w1d5-technical-explainer-comparison.ipynb` - Technical explainer with model comparison
- `utils.py` - HTML scraping utilities
- `requirements.txt` - Python dependencies
- `env.example` - Environment variable template

## Requirements

- Python 3.8+
- Ollama (for local inference)
- OpenRouter API key (for GPT models)
