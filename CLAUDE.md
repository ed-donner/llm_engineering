# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an 8-week LLM Engineering course repository by Ed Donner. Each week builds toward an autonomous agentic AI solution in Week 8. The course uses Jupyter notebooks for hands-on learning with various LLM APIs and frameworks.

## Development Commands

```bash
# Package management (uses uv - https://docs.astral.sh/uv/)
uv sync                    # Install all dependencies
uv add <package>           # Add a new dependency (instead of pip install)
uv run <script.py>         # Run Python scripts (no need to activate venv)
uv self update             # Update uv itself

# Running notebooks
# Open in Cursor/VS Code, select kernel: .venv (Python 3.12.x)

# Running Python files directly
uv run week8/price_is_right.py
uv run week5/app.py

# Modal cloud deployments (Week 8)
uv run modal deploy week8/pricer_service.py
```

## Repository Structure

- `week1/` - `week8/`: Course modules with daily notebooks (`day1.ipynb`, `day2.ipynb`, etc.)
  - Each week has a `community-contributions/` or `community_contributions/` folder for student projects
  - Week exercises: `week1 EXERCISE.ipynb`, `week2 EXERCISE.ipynb`
- `guides/`: Supplementary tutorials (numbered 01-14) covering Python, notebooks, APIs, debugging
- `setup/`: Platform-specific setup instructions and troubleshooting
- `extras/`: Additional materials

## Key Technologies

- **LLM APIs**: OpenAI, Anthropic Claude, Google Gemini, Ollama (local)
- **Frameworks**: LangChain (with langchain-openai, langchain-anthropic, langchain-chroma, langchain-ollama)
- **Vector DB**: ChromaDB for RAG implementations
- **Cloud**: Modal for serverless deployments, Google Colab for GPU work (Weeks 3, 7)
- **UI**: Gradio for web interfaces
- **ML**: PyTorch, Transformers, sentence-transformers, scikit-learn, XGBoost

## Environment Configuration

API keys are stored in `.env` file in project root:
```
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
```

## Week 8 Agent Architecture

The capstone project in `week8/` implements an autonomous deal-finding agent:
- `agents/`: Agent implementations (frontier_agent, planning_agent, scanner_agent, etc.)
- `deal_agent_framework.py`: Core orchestration framework
- `price_is_right.py`: Main application entry point
- `pricer_service.py`: Modal-deployed pricing service

## Python Version

Python 3.12 (specified in `.python-version`)

## Use Latest Technology (as of 2026-01-14)

Always use the latest available versions of models, libraries, software, and tools when writing code for this project:

**AI Models:**
- **OpenAI**: Use `gpt-5-nano` for cost-effective tasks, `gpt-5` for complex reasoning
- **Anthropic**: Use `claude-opus-4-5` for complex tasks, `claude-sonnet-4` for general use
- Avoid outdated models like `gpt-4o-mini`, `gpt-3.5-turbo`, or older Claude versions

**Libraries & Frameworks:**
- Always prefer the latest stable versions of Python packages
- Use current API patterns and syntax (e.g., OpenAI's latest client syntax, not deprecated patterns)
- Check for and use modern alternatives to deprecated functions

**General Principle:**
- If unsure about the latest version, ask the user or search for current documentation
- Avoid defaulting to older versions from training data
- When in doubt, verify what's current before writing code

<!-- SESSION_HANDOFF_START -->
## Session Handoff

**Current handoff document**: `NEXT_SESSION_PROMPT_2026-01-14_1733.md`

At the start of a new session, read the handoff document above and `IMPLEMENTATION_PLAN.md` for context.
<!-- SESSION_HANDOFF_END -->

---

**Last Updated**: 2026-01-14
**Last Session**: Created Selenium sentiment analyzer for Week 1 community contribution
