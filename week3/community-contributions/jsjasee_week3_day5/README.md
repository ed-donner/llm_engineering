# FinSynth Ledger Lab

FinSynth Ledger Lab is a small Gradio app for generating fake finance datasets that look realistic enough for demos, practice projects, and testing. It is built for people who want synthetic bank-style data without using real customer records. The project supports a few preset dataset types, sends a prompt to a language model, checks the returned JSON, turns it into a pandas DataFrame, and saves it as a CSV file.

This project exists to make synthetic data generation easier for beginners. Instead of wiring together prompt logic, JSON parsing, validation, and a user interface from scratch, the notebook gives you a simple starting point you can run, inspect, and customize. The code is intentionally small, so you can understand each part without digging through a large codebase.

## Table of Contents

- [Executive Summary](#executive-summary)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Setup Guide](#setup-guide)
- [Usage Guide](#usage-guide)
- [Code Walkthrough](#code-walkthrough)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [FAQ and Troubleshooting](#faq-and-troubleshooting)
- [License and Credits](#license-and-credits)

## Executive Summary

This project generates synthetic finance records through a notebook-driven Gradio interface. Users choose a dataset preset such as a personal bank statement or company expense ledger, pick a model, set row count and temperature, then click a button to generate fake JSON data. The app validates the response, shows it in a table, and saves a downloadable CSV.

The main benefit is that the project separates the workflow into clear steps: define a schema, build a prompt, call a model, validate the output, convert it into a table, and present it in a UI. That makes it useful both as a working tool and as a learning example for junior developers exploring Gradio, prompt-based data generation, and simple validation pipelines.

## Architecture Overview

### High-level Flow

```text
User in Gradio UI
    |
    v
Select preset + model + row count + temperature + prompt
    |
    v
run_generation_pipeline()
    |
    +--> build_dataset_prompt()
    |
    +--> generate_raw_json()
           |
           +--> generation_runner.py
                   |
                   +--> generation_messages.py
                   +--> model_options.py
                   +--> OpenAI or Hugging Face client
    |
    v
json_to_dataframe()
    |
    +--> validate_dataset_rows()
    +--> save_csv()
    |
    v
Show DataFrame + JSON + CSV download in Gradio
```

### Components

| Component            | File                         | What it does                                                                           |
| -------------------- | ---------------------------- | -------------------------------------------------------------------------------------- |
| Notebook app         | `finsynth_ledger_lab.ipynb`  | Contains the main workflow, dataset presets, validation, pipeline logic, and Gradio UI |
| Model registry       | `model_options.py`           | Stores available model choices and helper functions for looking them up                |
| Prompt builder       | `generation_messages.py`     | Builds the system and user messages sent to the selected model                         |
| Model runner         | `generation_runner.py`       | Calls either Hugging Face or OpenAI and returns generated JSON text                    |
| Sample output target | `synthetic_finance_data.csv` | Created when generation succeeds                                                       |

### Current Dataset Presets

| Preset                   | Purpose                                                   | Fields                                                               |
| ------------------------ | --------------------------------------------------------- | -------------------------------------------------------------------- |
| Personal bank statement  | Simulates simple transaction history with running balance | `date`, `working`, `description`, `withdrawal`, `deposit`, `balance` |
| Credit card spending log | Simulates card transactions                               | `date`, `description`, `amount_spent`                                |
| Company expense ledger   | Simulates business expenses                               | `date`, `description`, `amount_spent`                                |

## Project Structure

```text
jsjasee_week3_day5/
|-- finsynth_ledger_lab.ipynb
|-- model_options.py
|-- generation_messages.py
|-- generation_runner.py
|-- finsynth_ledger_lab_checklist.md
`-- README.md
```

## Setup Guide

### Prerequisites

- Python 3.10 or newer
- A valid OpenAI API key if you want to use `gpt-4.1-mini`
- A Hugging Face token if your Hugging Face usage requires authentication
- Jupyter Notebook or JupyterLab

### Install

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required packages used by the notebook:

```bash
pip install gradio pandas openai huggingface_hub python-dotenv jupyter
```

### Configure

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
HF_TOKEN=your_huggingface_token_here
```

Notes:

- `OPENAI_API_KEY` is needed for the OpenAI model option.
- `HF_TOKEN` may be optional depending on your Hugging Face access and rate limits, but it is a good idea to set it.
- Do not commit `.env` to version control.

### Run

Start Jupyter:

```bash
jupyter notebook
```

Open `finsynth_ledger_lab.ipynb`, then run the cells from top to bottom. The last cell launches the Gradio app in your browser:

```python
app.launch(inbrowser=True)
```

### Test the setup

Basic setup is working if:

- the imports run without errors
- the OpenAI and Hugging Face clients are created successfully
- the Gradio UI opens
- generating a small 5-row dataset returns JSON and a table

## Usage Guide

### How to use the app

1. Run the notebook from top to bottom.
2. In the Gradio UI, choose a dataset type.
3. Choose a generation model.
4. Set `Row count`.
5. Set `Temperature`.
6. Review or edit the prompt.
7. Keep JSON checks enabled unless you intentionally change the schema.
8. Click `Generate`.

The app returns:

- a DataFrame preview
- the generated JSON
- a downloadable CSV file
- a status message

### Example: generate a personal bank statement

Typical UI settings:

| Setting            | Example value             |
| ------------------ | ------------------------- |
| Dataset type       | `Personal bank statement` |
| Generation model   | `Qwen 2.5 72B Instruct`   |
| Row count          | `5`                       |
| Temperature        | `0.4`                     |
| Enable JSON checks | `true`                    |

Prompt example:

```text
Generate exactly 5 rows of synthetic personal bank statement data.
Return JSON only as a list of objects.
Required fields: date, working, description, withdrawal, deposit, balance.
Include realistic variety from: salary, groceries, food, transport, subscriptions, transfers, refunds.
Rules:
- Return JSON only.
- Use fake synthetic financial activity only.
- Keep the running balance internally consistent.
- Working has only TWO values, Debit or Credit. Data type is string.
- You should use the categories only as a guide, generate new categories or even use specific merchant names to make it more realistic.
Do not include real personal data, real account numbers, or explanations.
```

Expected result:

- JSON list of objects
- matching columns in the DataFrame
- CSV saved as `synthetic_finance_data.csv`

### Example: programmatic use inside the notebook

You can also call the pipeline directly from a notebook cell:

```python
result = run_generation_pipeline(
    dataset_type="credit_card_spending_log",
    row_count=5,
    temperature=0.4,
    model_key=DEFAULT_MODEL_KEY,
)

result["dataframe"]
result["clean_json"]
result["csv_path"]
result["warning"]
```

### CLI or API support

This project does not currently expose:

- a command-line interface
- REST API endpoints
- a packaged Python module

The primary interface is the Gradio app launched from the notebook.

## Code Walkthrough

This section explains the main functions in plain language.

### 1. Dataset preset registry

Defined in the notebook through `DATASET_PRESETS`.

What it does:

- stores the available dataset types
- defines each dataset label
- lists the required fields
- lists category examples
- lists prompt rules

Why it matters:

- this is the source of truth for schema and prompt behavior
- if you want to add a new dataset type, this is the first place to edit

Related function:

```python
def get_dataset_preset(dataset_type):
```

This function fetches the preset and raises an error if the key is unknown.

### 2. Prompt builder

Main notebook function:

```python
def build_dataset_prompt(dataset_type, row_count):
```

What it does:

- checks that `row_count` is positive
- reads the chosen preset
- builds a plain-English prompt with:
  - exact row count
  - required fields
  - example categories
  - preset rules
  - privacy reminder

The helper module `generation_messages.py` adds a stricter system message around that prompt before the model call. Its main function is:

```python
def build_generation_messages(model_key, preset, prompt):
```

That function:

- looks up the selected model
- turns preset fields and rules into a system instruction
- tells the model to return valid JSON only
- returns a two-message list: one system message and one user message

### 3. Model selection

Defined in `model_options.py`.

Important values:

- `MODEL_OPTIONS`: available models and providers
- `DEFAULT_MODEL_KEY`: default choice used in the notebook
- `get_model_option(model_key)`: validates a model key and returns its config
- `get_model_labels()`: maps UI labels back to internal keys

Why it matters:

- it keeps model details out of the UI code
- adding another model is mostly a config change here

### 4. Raw JSON generation

Notebook wrapper:

```python
def generate_raw_json(dataset_type, prompt, temperature, max_tokens, model_key=DEFAULT_MODEL_KEY):
```

This function gets the chosen preset and forwards the request to `generation_runner.py`.

The helper file function:

```python
def generate_raw_json(
    dataset_type,
    prompt,
    temperature,
    max_tokens,
    preset,
    model_key,
    hf_client,
    openai_client,
):
```

What it does:

- builds model messages
- checks which provider the chosen model belongs to
- calls Hugging Face if provider is `huggingface`
- calls OpenAI if provider is `openai`
- returns the raw text response

Important note:

- `dataset_type` is passed in but not directly used in the helper runner right now
- the actual generation behavior is driven by `preset`, `prompt`, and `model_key`

### 5. Validation

Main function:

```python
def validate_dataset_rows(dataset_type, rows, enabled_check=True):
```

What it checks:

- output is a list
- each row is a dictionary
- fields match the expected schema exactly
- `working` is `Debit` or `Credit` for bank statements
- `amount_spent` is numeric for the other two presets

Why the checkbox exists:

- if users modify the prompt and produce a different schema, strict validation will fail
- unchecking `Enable JSON checks` lets the UI show whatever valid JSON columns the model returned

### 6. JSON to DataFrame conversion

Main function:

```python
def json_to_dataframe(clean_json, dataset_type=None, enabled_check=True):
```

What it does:

- parses the JSON text using `json.loads()`
- converts the parsed rows into a pandas DataFrame
- optionally validates rows against the preset schema
- reorders columns to match the expected field order
- returns either `(df, None)` on success or `(None, error_message)` on failure

### 7. CSV export

Main function:

```python
def save_csv(df, filename="synthetic_finance_data.csv"):
```

What it does:

- checks that the DataFrame is not empty
- writes it to a CSV file in the project directory
- returns the saved file path

### 8. End-to-end pipeline

Main function:

```python
def run_generation_pipeline(...):
```

This is the main orchestration function. It:

- builds or accepts a prompt
- calls the selected model
- parses the returned JSON
- validates it
- saves a CSV if parsing succeeds
- returns one dictionary containing everything the UI needs

Returned keys:

- `prompt`
- `raw_text`
- `clean_json`
- `dataframe`
- `csv_path`
- `warning`

### 9. Gradio UI

Main function:

```python
def build_gradio_app():
```

What it creates:

- dataset dropdown
- model dropdown
- row count slider
- temperature slider
- prompt textbox
- validation checkbox
- generate button
- DataFrame preview
- JSON output box
- file download component
- status box

Event flow:

- changing dataset or row count updates the default prompt
- clicking `Generate` runs `run_generation_pipeline()`
- results are displayed in the UI

## Configuration

### Environment variables

| Variable         | Required                  | Purpose                                            |
| ---------------- | ------------------------- | -------------------------------------------------- |
| `OPENAI_API_KEY` | Required for OpenAI model | Authenticates requests to OpenAI                   |
| `HF_TOKEN`       | Recommended               | Authenticates requests to Hugging Face when needed |

### Config values in code

| Name                | Location           | Purpose                                   |
| ------------------- | ------------------ | ----------------------------------------- |
| `MAX_TOKENS`        | Notebook           | Caps output length for model generation   |
| `DATASET_PRESETS`   | Notebook           | Defines available dataset types and rules |
| `DEFAULT_MODEL_KEY` | `model_options.py` | Chooses the default model                 |
| `MODEL_OPTIONS`     | `model_options.py` | Lists available model configs             |

### Secrets handling

- keep secrets in `.env`
- load them with `load_dotenv()`
- never hard-code API keys in notebook cells or helper files
- add `.env` to `.gitignore` if it is not already ignored

## FAQ and Troubleshooting

### Why does generation fail with an authentication error?

Most likely cause:

- `OPENAI_API_KEY` or `HF_TOKEN` is missing or invalid

Fix:

- check your `.env` file
- restart the notebook kernel after updating environment variables

### Why do I get `Unknown model`?

Most likely cause:

- the selected or hard-coded model key is not present in `MODEL_OPTIONS`

Fix:

- check `model_options.py`
- use one of the supported keys exactly as defined

### Why does JSON parsing fail?

Most likely cause:

- the model returned extra text, invalid JSON, or partial output

Fix:

- reduce `row_count`
- keep the prompt strict
- lower temperature
- try another model
- increase `MAX_TOKENS` if output is being cut off

### Why do I see schema validation errors after editing the prompt?

Most likely cause:

- the prompt now asks for fields that do not match the preset schema

Fix:

- either restore the original schema
- or uncheck `Enable JSON checks` so the UI can display the modified JSON structure

### Why is the CSV file missing?

Most likely cause:

- DataFrame creation failed, so `save_csv()` never ran

Fix:

- inspect the warning/status box
- inspect the generated JSON output
- fix parsing or validation problems first

### Why does the Gradio app not open?

Possible causes:

- notebook cells were not run in order
- `gradio` is not installed
- the kernel is in a bad state

Fix:

- restart the kernel
- rerun all cells
- confirm imports succeed

### Credits

- Built with [Gradio](https://www.gradio.app/)
- Uses [pandas](https://pandas.pydata.org/) for tabular data handling
- Uses [OpenAI](https://platform.openai.com/) and [Hugging Face](https://huggingface.co/) model APIs for generation
