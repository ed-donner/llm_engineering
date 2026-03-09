# Study Resource Scout Agent

Study Resource Scout is a Week 8 style autonomous tool-using agent project that scans and scores learning resources for a topic, then returns the top 5 candidates.

## Architecture

- `AutonomousPlanningAgent`: tool-calling loop (`scan`, `estimate`) and rank top 5
- `ScannerAgent`: collects and filters candidates from feeds, with fallback resources
- `EnsembleAgent`: computes quality score from domain trust + keyword match + snippet richness
- `ResourceScoutFramework`: autonomous orchestration + memory-backed dedupe

## Project Structure

- `launcher.py` entrypoint commands (`run`, `autorun`, `ui`)
- `ui.py` minimal Gradio interface
- `resource_agent_framework.py` framework + persistence
- `agents/` all agent implementations and resource models
- `memory.json` persisted dedupe history

## Setup

Requirements workflow (run from this `jamal-ishaq` directory):

Freeze current environment into `requirements.txt`:
```bash
pip freeze > requirements.txt
```

Install dependencies from file:
```bash
pip install -r requirements.txt
```

Optional environment variables:

- `OPENROUTER_API_KEY` (enables LLM-backed autonomous tool loop)
- `OPENROUTER_BASE_URL` (optional, defaults to `https://openrouter.ai/api/v1`)
- `OPENROUTER_MODEL` (optional, defaults to `openai/gpt-4o-mini`)

Without `OPENROUTER_API_KEY`, autonomous mode uses a deterministic fallback policy so it still runs.

## Usage

From this directory:

```bash
python launcher.py run --topic "llm evals"
python launcher.py ui
```

## How memory works

- UI table shows the latest run's top 5 candidates only.
- `memory.json` stores URLs from prior runs for scanner deduplication.
- New unique URLs from the latest top 5 are merged into memory.
