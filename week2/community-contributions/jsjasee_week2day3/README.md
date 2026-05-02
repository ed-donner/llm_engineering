# Pre-Mortem Bot

Small notebook project that turns an LLM into a blunt pre-mortem facilitator for project ideas.

It takes a project description, assumes the project failed six months after launch, then asks focused questions about likely failure modes across scope, timeline, stakeholders, and external risks. The notebook runs this through a simple Gradio chat interface.

## File

- `pre-mortem-bot.ipynb` - main notebook with prompt setup, few-shot examples, streaming chat callback, and Gradio UI

## Requirements

```bash
pip install openai python-dotenv gradio
```

## Environment

Create a `.env` file with:

```env
OPENAI_API_KEY=your_openai_key
```

## Run

Open and run the notebook:

```bash
jupyter notebook "/Users/tayjiasheng/AI Projects/llm_engineering/week2/community-contributions/jsjasee_week2day3/pre-mortem-bot.ipynb"
```

The notebook uses `gpt-4.1-mini` and launches a Gradio `ChatInterface`.

## What It Does

- loads an OpenAI API key from `.env`
- uses a strong system prompt plus 2 few-shot examples
- streams responses from the model
- keeps replies short, critical, and action-oriented

## Output Style

The bot is designed to:

- identify 2 to 3 likely failure causes
- ask numbered follow-up questions
- avoid giving solutions too early
- end with one concrete de-risking action for the week
