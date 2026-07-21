# Prompt Experiment Runner

A lightweight framework for running and managing LLM prompt experiments using structured data validation with Pydantic and generator-based processing pipelines.

## Overview

This project was created as a hands-on exercise to learn and apply several intermediate Python concepts that are highly relevant to LLM engineering:

- Pydantic models
- Generators
- Type hints
- Structured data validation
- Modular project design

The application loads prompt experiments from a JSON file, validates them using Pydantic, executes them against an LLM, and stores the results in a structured JSON output file.

---

## Learning Objectives

This project explores two key concepts used extensively in modern AI applications:

### Pydantic

Pydantic provides validation and structure for application data.

It is used to:

- Validate experiment inputs
- Restrict task types to allowed values
- Ensure required fields are present
- Create structured output objects for experiment results

### Generators

Generators allow experiments to be processed one at a time instead of loading everything into memory at once.

The project uses generators to:

- Stream experiment records from disk
- Process experiments sequentially
- Build scalable data-processing pipelines

---

## Features

- Load prompt experiments from JSON
- Validate experiment definitions using Pydantic
- Restrict tasks to approved task types
- Process experiments through a generator-based pipeline
- Run experiments against an LLM
- Save structured experiment results to JSON
- Modular project architecture

---

## Project Structure

```text
promptexperimentrunner/
├── experiments.json
├── results.json
├── loader.py
├── main.py
├── models.py
├── runner.py
├── writer.py
└── README.md
```

### File Descriptions

| File | Purpose |
|--------|---------|
| models.py | Pydantic data models |
| loader.py | Loads and validates experiments |
| runner.py | Executes experiments against an LLM |
| writer.py | Saves structured results |
| main.py | Orchestrates the application |
| experiments.json | Experiment definitions |
| results.json | Experiment results |

---

## Supported Task Types

Current experiment categories include:

- research_summary
- email_review
- meeting_actions
- risk_review
- rewrite

These task types are validated using Pydantic literals to prevent invalid experiment definitions.

---

## Example Experiment

```json
{
  "name": "Executive Summary",
  "task_type": "research_summary",
  "system_prompt": "You are a helpful assistant who reviews research articles and generates summaries.",
  "user_input": "Researchers analyzed the impact of electric vehicle adoption in urban environments..."
}
```

---

## Example Output

```json
{
  "experiment_name": "Executive Summary",
  "task_type": "research_summary",
  "response": "The study found that electric vehicle adoption reduced emissions and improved air quality..."
}
```

---

## How It Works

```text
experiments.json
        ↓
load_experiments()
        ↓
Pydantic validation
        ↓
Generator pipeline
        ↓
LLM execution
        ↓
ExperimentResult
        ↓
results.json
```

---

## Key Takeaways

This project demonstrates how:

- Pydantic can be used to enforce data quality and create reliable application boundaries
- Generators enable efficient, scalable processing pipelines
- Structured inputs and outputs improve maintainability
- Modular design leads to cleaner, more testable code

---

## Future Improvements

Potential enhancements include:

- Support for JSONL datasets
- Batch experiment execution
- Multiple model comparisons
- Prompt version tracking
- Experiment scoring and evaluation
- Result visualization
- Async execution

---

## Author

Teja Chatty

Created as a self-study project while learning intermediate Python concepts and LLM engineering patterns.