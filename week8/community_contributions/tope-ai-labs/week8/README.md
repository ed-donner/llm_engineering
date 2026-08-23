# Simple Multi-Agent (tope-ai-labs, Week 8)

A minimal multi-agent pipeline based on the week8 exercises: **Coordinator** orchestrates **Researcher** → **Analyzer** → **Reporter**. Can run locally or on **Modal**.

## Structure

- **CoordinatorAgent** – Orchestrator (same idea as week8 `PlanningAgent`).
- **ResearcherAgent** – Gathers/summarizes a topic (Scanner-style).
- **AnalyzerAgent** – Extracts key points (processing-style).
- **ReporterAgent** – Formats final output (Messaging-style).

## Notebook

Open **`simple_multi_agent.ipynb`** and run the cells. Start from the **week8/** directory so paths resolve. The notebook runs the pipeline locally (mock or LLM) and optionally via Modal.

## Run locally (script)

From **week8** directory:

```bash
cd week8
python community_contributions/tope-ai-labs/week8/simple_multi_agent.py
python community_contributions/tope-ai-labs/week8/simple_multi_agent.py "climate change and AI"
```

## Optional: use real LLM (local)

Set `USE_LLM=true` and `OPENAI_API_KEY` in `.env`. Otherwise agents use mock responses.

```bash
USE_LLM=true python community_contributions/tope-ai-labs/week8/simple_multi_agent.py "multi-agent systems"
```

## Modal implementation

The pipeline can run on Modal (OpenAI calls happen in the cloud; no GPU).

### 1. Deploy the Modal app

From **week8**:

```bash
cd week8
modal deploy community_contributions/tope-ai-labs/week8/modal_multi_agent.py
```

### 2. Modal secret (OpenAI)

In the [Modal dashboard](https://modal.com/secrets), create a secret named **`openai-api-key`** with your `OPENAI_API_KEY`. Or reuse an existing OpenAI secret and change `secrets` in `modal_multi_agent.py` to that name.

### 3. Run via Modal

From **week8**:

```bash
USE_MODAL=true python community_contributions/tope-ai-labs/week8/simple_multi_agent.py "multi-agent systems"
```

Or from Python:

```python
import modal
Pipeline = modal.Cls.lookup("tope-ai-labs-multi-agent", "MultiAgentPipeline")
report = Pipeline().run.remote("your topic here")
print(report)
```

## Dependencies

- Python 3.x
- `python-dotenv` (for `.env`)
- Optional: `openai` for local LLM mode
- Optional: `modal` for Modal deployment and `USE_MODAL=true` runs
