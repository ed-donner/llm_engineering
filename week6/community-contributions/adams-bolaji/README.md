# Job Salary Estimator

A capstone project that predicts job salary from job descriptions, modeled after the Week 6 "The Price Is Right" pipeline.

**Dataset**: [lukebarousse/data_jobs](https://huggingface.co/datasets/lukebarousse/data_jobs) – 785K+ data analytics job postings from 2023.

## Project Structure

```
adams-bolaji/
├── job_salary/           # Core package
│   ├── items.py         # Job model (like pricer's Item)
│   ├── parser.py        # Parse data_jobs datapoints
│   ├── evaluator.py     # Salary-specific evaluation
│   ├── loaders.py       # Load from HuggingFace
│   └── batch.py         # Groq batch API for LLM rewriting
├── jsonl/               # Fine-tuning files (created on Day 5)
├── day1.ipynb           # Data curation
├── day2.ipynb           # Data pre-processing (LLM rewriting)
├── day3.ipynb           # Evaluation, baselines, traditional ML
├── day4.ipynb           # Deep learning, frontier LLMs
├── day5.ipynb           # Fine-tuning GPT-4.1-nano
└── README.md
```

## Setup

1. From the project root (`llm_engineering`), ensure deps are installed:
   ```bash
   uv sync
   ```

2. Add to `.env` (or environment):
   - `HF_TOKEN` – HuggingFace token (for dataset access)
   - `GROQ_API_KEY` – optional, for batch pre-processing
   - `OPENAI_API_KEY` – for Day 4 LLMs and Day 5 fine-tuning
   - `ANTHROPIC_API_KEY` – optional, for Claude in Day 4

3. Run notebooks from `week6/adams-bolaji`:
   ```bash
   cd week6/adams-bolaji
   jupyter notebook
   ```


## Evaluation

The evaluator uses salary-specific thresholds:
- **Green**: error < $12k or < 15% of actual salary
- **Orange**: error $12k–$25k or 15–30%
- **Red**: error > $25k or > 30%

Metric: Mean Absolute Error (MAE) in dollars.
