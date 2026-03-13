# Week 8 — Multi-Agent Price Predictor

Week 8 builds a full agent framework deployed on Modal.com with a fine-tuned Llama model.
This is a simplified local version using the same agent architecture without needing Modal or a GPU.

## Agents

| Agent | What it does |
|-------|-------------|
| **SpecialistAgent** | Few-shot expert — shows the LLM 8 real price examples before asking (simulates the fine-tuned model) |
| **FrontierAgent** | Chain-of-thought reasoner — thinks through category, features, and price range step by step |
| **EnsembleAgent** | Combines both estimates with a weighted average (55% Frontier, 45% Specialist) |

## Setup

Add your OpenAI API key to `.env`:

```
OPENAI_API_KEY=sk-...
```

Install dependencies:

```bash
pip install openai gradio datasets python-dotenv tqdm
```

## Usage

Run all cells in `multi_agent_pricer.ipynb` top to bottom.

The Gradio UI shows each agent's individual estimate alongside the final ensemble answer.
