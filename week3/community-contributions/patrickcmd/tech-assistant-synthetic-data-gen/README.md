# Technical Assistant Dataset Generator

Generates synthetic conversational datasets for training AI assistants aimed at AI Engineers.

Each generated datapoint contains:

| Column | Description |
|---|---|
| `system_prompt` | Instruction defining assistant behavior |
| `prompt` | Realistic user question |
| `completion` | Detailed assistant response |

## Supported Models

| Model | Provider |
|---|---|
| `gpt-4.1-mini` | OpenAI |
| `openai/gpt-oss-120b` | Groq |
| `llama3.2` | Ollama (local) |

## Engineer Levels

- **Beginner** — educational, conceptual explanations
- **Intermediate** — practical, code-oriented
- **Advanced** — architecture, scaling, optimization
- **Research** — theoretical depth, paper references

## Setup

```bash
cd synthentic-data-generator

uv pip install -r requirements.txt

cp .env.example .env
# Edit .env with your API keys
```

For Ollama, make sure the server is running locally:

```bash
ollama serve
ollama pull llama3.2
```

## Run

```bash
uv run app.py
```

Opens a Gradio UI at `http://localhost:7860` where you can:

1. Select a model, engineer level, and topic
2. Set dataset size and temperature
3. Click **Generate Dataset** to create data
4. Preview the results in-browser
5. Optionally upload to HuggingFace Hub

## Project Structure

```
schemas.py         — Pydantic models (DataPoint, SyntheticDataset)
llm_clients.py     — OpenAI/Groq/Ollama client setup
prompt_builder.py  — System prompt templates per level & topic
generator.py       — Batch generation pipeline with validation
hf_uploader.py     — HuggingFace dataset upload
app.py             — Gradio UI (entry point)
```