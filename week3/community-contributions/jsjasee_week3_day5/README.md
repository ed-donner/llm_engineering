# FinSynth Ledger Lab — Generate fake finance datasets from a notebook

## Overview
A Gradio notebook app for creating synthetic finance datasets.
Use it to generate fake bank-style records without real customer data.

## Features
- Generate synthetic finance rows
- Choose dataset presets
- Select OpenAI or Hugging Face models
- Validate returned JSON
- Preview data in Gradio
- Export results as CSV

## Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install gradio pandas openai huggingface_hub python-dotenv jupyter
```

## Usage
Run the notebook, then launch the Gradio app.

```python
# Open finsynth_ledger_lab.ipynb
# Run all cells from top to bottom

app.launch(inbrowser=True)
```

Common UI settings:

```text
Dataset type: Personal bank statement
Generation model: Qwen 2.5 72B Instruct
Row count: 5
Temperature: 0.4
Enable JSON checks: true
```

## Configuration
| Name | Default | What it does |
| --- | --- | --- |
| `OPENAI_API_KEY` | none | Enables OpenAI model calls |
| `HF_TOKEN` | none | Enables authenticated Hugging Face calls |
| `DEFAULT_MODEL_KEY` | set in `model_options.py` | Selects the default model |
| `MODEL_OPTIONS` | set in `model_options.py` | Lists available models |
| `DATASET_PRESETS` | set in notebook | Defines dataset types and fields |
| `MAX_TOKENS` | set in notebook | Limits generated output length |
