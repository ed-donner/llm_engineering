# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an 8-week LLM Engineering course repository from Ed Donner's Udemy course. The course teaches students to build AI applications using LLMs, culminating in an autonomous multi-agent AI system in Week 8. The repository contains Jupyter notebooks organized by week, each with daily labs that students execute while learning.

## Repository Structure

- `week1/` through `week8/`: Weekly course modules, each containing daily notebooks (`day1.ipynb`, `day2.ipynb`, etc.)
- `guides/`: Reference notebooks covering foundational topics (Python, Git, notebooks, debugging, APIs, etc.)
- `setup/`: Setup instructions and troubleshooting notebooks for different platforms
- `community-contributions/`: Student project submissions and variations
- `week8/agents/`: Multi-agent system implementation for the final project ("The Price is Right")

## Technology Stack

- **Language**: Python 3.11+ (configured in `.python-version`)
- **Environment**: Virtual environment managed via `uv` or traditional venv (`.venv/`)
- **Primary Libraries**:
  - LLM APIs: `openai`, `anthropic`, `google-generativeai`, `groq`
  - LangChain ecosystem: `langchain`, `langchain-openai`, `langchain-chroma`, etc.
  - ML/Data: `torch`, `transformers`, `scikit-learn`, `pandas`, `numpy`
  - Local models: `ollama`
  - Cloud deployment: `modal`
  - UI: `gradio` (pinned to v5.x)
  - Utilities: `litellm`, `beautifulsoup4`, `chromadb`, `sentence-transformers`

## Development Workflow

### Environment Setup

The repository uses `uv` as the modern Python package manager, but also supports traditional pip:

```bash
# Using uv (preferred)
uv sync
uv run jupyter lab

# Traditional approach
pip install -r requirements.txt
jupyter lab
```

### API Keys Configuration

All API keys are stored in `.env` file (NOT committed to git). Required keys depend on which weeks/exercises you're working on:

- `OPENAI_API_KEY`: Required for most exercises (starts with `sk-proj-`)
- `ANTHROPIC_API_KEY`: Optional, for Claude models (starts with `sk-ant-`)
- `GOOGLE_API_KEY`: Optional, for Gemini models
- `DEEPSEEK_API_KEY`, `GROQ_API_KEY`, `GROK_API_KEY`, `OPENROUTER_API_KEY`: Optional
- `HF_API_KEY` or `HF_TOKEN`: For HuggingFace models (used in later weeks)
- `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`: For Week 8 cloud deployment

After modifying `.env`, always reload with:
```python
from dotenv import load_dotenv
load_dotenv(override=True)
```

### Running Notebooks

1. Open Jupyter Lab: `uv run jupyter lab` (or `jupyter lab`)
2. Navigate to the week folder (e.g., `week1/`)
3. Open the day's notebook (e.g., `day1.ipynb`)
4. Select the kernel: Choose `.venv (Python 3.12.x)` from the kernel selector
5. Execute cells in order from top to bottom (Shift+Enter)

### Working with Ollama (Local Models)

For running local LLMs without API costs:

```bash
# Start Ollama server (in separate terminal)
ollama serve

# Pull a model
ollama pull llama3.2

# In Python notebooks, connect via:
# ollama = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
```

### Week 8 Specific: Modal.com Deployment

Week 8 involves deploying models to Modal.com cloud infrastructure:

```bash
# Set up Modal credentials (run once)
uv run modal token set --token-id ak-xxx --token-secret as-xxx

# Deploy a service
uv run modal deploy -m pricer_service

# In Python, call deployed functions:
# pricer = modal.Function.from_name("pricer-service", "price")
# result = pricer.remote(input_text)
```

Modal secrets (e.g., HuggingFace tokens) must be configured via Modal's web dashboard at modal.com/secrets.

## Course Progression

### Week 1: Introduction and API Basics
- First LLM API calls (OpenAI)
- Web scraping and summarization
- Prompt engineering basics
- File: `scraper.py` contains website content fetching utilities

### Week 2: Multiple LLM APIs and Conversation
- Connecting to Anthropic, Gemini, DeepSeek, Groq
- Conversation history management with message lists
- Multi-agent conversations
- Using abstraction layers (LiteLLM, LangChain)
- Prompt caching techniques

### Week 3: Synthetic Data and Fine-tuning Setup
- Uses Google Colab for GPU access
- Synthetic data generation
- Dataset preparation

### Week 4-5: RAG and Knowledge Bases
- Vector databases (ChromaDB)
- Embeddings with sentence-transformers
- Retrieval-Augmented Generation patterns

### Week 6-7: Model Training
- Fine-tuning LLMs
- Uses Google Colab Pro for GPU-intensive work
- Training/validation dataset handling

### Week 8: Multi-Agent System - "The Price is Right"
The culminating project with 7 specialized agents:

**Agent Architecture** (`week8/agents/`):
- `agent.py`: Base agent class
- `specialist_agent.py`: Product pricing specialist using fine-tuned model
- `preprocessor.py`: Text preprocessing for consistent input
- `frontier_agent.py`: Uses frontier models (GPT-5, Claude) for complex reasoning
- `ensemble_agent.py`: Combines multiple agent predictions
- `scanner_agent.py`: Web scraping and market research
- `messaging_agent.py`: Handles agent-to-agent communication
- `autonomous_planning_agent.py`: Creates and executes multi-step plans
- `neural_network_agent.py`, `deep_neural_network.py`: ML-based pricing
- `evaluator.py`: Evaluates agent performance
- `items.py`, `deals.py`: Data structures for products and deals

**Key Files**:
- `deal_agent_framework.py`: Orchestrates all agents
- `price_is_right.py`: Main entry point for the multi-agent system
- `pricer_service.py`, `pricer_service2.py`: Modal deployment configurations
- `pricer_ephemeral.py`: Local testing before deployment
- `hello.py`, `llama.py`: Modal introduction examples
- `memory.json`: Agent state persistence

## Common Patterns

### Message Format for LLM APIs
All major LLM APIs use this structure:
```python
messages = [
    {"role": "system", "content": "System instructions here"},
    {"role": "user", "content": "User message"},
    {"role": "assistant", "content": "Assistant response"},
    {"role": "user", "content": "Follow-up message"}
]
```

### Using Multiple LLM Providers via OpenAI Client
```python
from openai import OpenAI

# Different providers, same interface
anthropic = OpenAI(api_key=key, base_url="https://api.anthropic.com/v1/")
gemini = OpenAI(api_key=key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
deepseek = OpenAI(api_key=key, base_url="https://api.deepseek.com")
```

### Cost Management
- Use cheaper models for development: `gpt-4.1-nano`, `claude-3-5-haiku-latest`, `gemini-2.5-flash-lite`
- Monitor usage at provider dashboards (links in README.md)
- Leverage prompt caching for repeated prompts
- Consider Ollama for free local inference

## Git Workflow

**IMPORTANT: This repository has custom git configuration. See `.cursor/rules` for complete details.**

### Multi-Account GitHub Setup (Critical!)
This user has multiple GitHub accounts configured via SSH aliases:
- **This repo uses**: `github.com-personal` (user: shabsi4u)
- **NEVER use** plain `github.com` in git commands - always use the aliased hostname

### Repository Structure
- **origin**: `git@github.com-personal:shabsi4u/llm_engineering.git` (personal fork)
- **upstream**: `git@github.com-personal:ed-donner/llm_engineering.git` (Ed Donner's original)

### Custom Git Aliases (Pre-configured)

**PR Workflow Aliases:**
- `git sync` - Sync local main with upstream and push to fork
- `git new <branch-name>` - Create new feature branch from updated main
- `git pr-check` - Verify changes are scoped to community-contributions/shabsi4u/
- `git pr-ready` - Push branch and display PR creation URL
- `git rebase-main` - Rebase current branch on latest upstream/main
- `git cleanup` - Delete local branches merged to main

**Personal Fork Management Aliases:**
- `git save "message"` - Add, commit, and push directly to fork's main (for personal docs/changes)
- `git quick "message"` - Add, commit, and push to current branch
- `git cm "message"` - Add and commit (without pushing)
- `git amend` - Amend last commit with current changes and force push
- `git pushf` - Push current branch to origin

### Workflow Rules

**For PR Submissions (community contributions):**
1. **NEVER commit directly to main** - always use feature branches via `git new <branch>`
2. **PR scope constraint**: PRs must ONLY contain changes in `community-contributions/shabsi4u/`
3. **Before PR**: Run `git pr-check` to verify no out-of-scope changes
4. **Clear notebook outputs** before committing: Edit > Clear Outputs of All Cells

**For Personal Fork Changes (CLAUDE.md, .cursor/rules, personal notes):**
1. **Commit directly to main** using `git save "message"`
2. These changes stay in your fork only, not submitted as PRs to upstream
3. Run `git sync` regularly to pull Ed's latest course updates
4. Your personal files won't conflict - they only exist in your fork
5. If Ed updates a file you modified, resolve conflicts manually (rare)

Main branch: `main`

### Fork Maintenance Strategy

**Your fork's main branch contains:**
- ✅ All of Ed's course materials (synced from upstream)
- ✅ Your personal documentation (CLAUDE.md, .cursor/rules)
- ✅ Your community contributions (community-contributions/shabsi4u/)

**Staying in sync with upstream:**
Run `git sync` regularly (weekly or before starting new work) to pull Ed's latest updates. Your personal files won't conflict because they only exist in your fork. Course material updates will merge cleanly unless you've modified the same files Ed has updated.

**If merge conflicts occur:**
- For personal files (CLAUDE.md, .cursor/rules): `git checkout --ours <file>` (keep your version)
- For course files: `git checkout --theirs <file>` (keep Ed's version)
- Then: `git add . && git commit && git push origin main`

## Important Conventions

- **Notebook execution**: Always run cells top-to-bottom in sequence
- **Kernel selection**: Must select `.venv` kernel for each new notebook
- **Environment variables**: Reload `.env` after any changes with `load_dotenv(override=True)`
- **API costs**: Course designed for minimal spend (few cents per exercise)
- **Modal credits**: Week 8 uses Modal credits; can be costly if containers left running

## Troubleshooting

Common issues have solutions in `setup/troubleshooting.ipynb`:
- API key validation errors
- Import errors / module not found
- Kernel selection issues
- Environment variable loading
- Unicode/encoding issues (especially Windows)

## Educational Philosophy

The course emphasizes:
- Learning by doing: Execute every cell, inspect objects, experiment
- Business applications: Each week includes real-world use cases
- Community sharing: Students encouraged to submit variations via PR
- Progressive complexity: Weeks build on each other toward Week 8 finale