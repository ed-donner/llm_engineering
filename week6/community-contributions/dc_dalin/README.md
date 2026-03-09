# Week 6: Fine-Tuning GPT-4o-mini

**dc_dalin** - Demonstrating closed-source model fine-tuning

## Setup

```bash
pip install openai gradio plotly pandas python-dotenv
```

Set `OPENAI_API_KEY` in `.env`

## Notebooks

### 1. `fine_tune_setup.ipynb`
Fine-tunes GPT-4o-mini on trivia dataset (40 train / 10 val examples).
Saves model ID to `fine_tuned_model_id.txt`.

### 2. `trivia_challenge_with_finetuning.ipynb`
Gradio app comparing Human vs Base GPT-4o-mini vs Fine-tuned GPT-4o-mini.
Shows accuracy improvement and performance metrics.

## Usage

1. Run `fine_tune_setup.ipynb` → wait for fine-tuning to complete (~10-30 min)
2. Run `trivia_challenge_with_finetuning.ipynb` → launch Gradio interface

## Files

- `fine_tune_train.jsonl` - Training data (OpenAI chat format)
- `fine_tune_validation.jsonl` - Validation data
- `questions_dataset.json` - Evaluation questions
- `fine_tuned_model_id.txt` - Generated model ID (after step 1)

---

Addresses PR feedback: Demonstrates fine-tuning using OpenAI's closed-source GPT-4o-mini model with measurable performance comparison.
