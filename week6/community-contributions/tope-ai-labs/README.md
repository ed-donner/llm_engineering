# Tope AI Labs – Week 6

## Fine-Tune a Frontier Model: Natural Language → SQL

This folder contains a notebook that fine-tunes a modern frontier model (e.g. **GPT-4.1-nano**) to translate plain English into SQL queries.

**Example:**
- **User:** Show all customers created last week  
- **Model output:**
  ```sql
  SELECT * FROM customers
  WHERE created_at >= NOW() - INTERVAL '7 days';
  ```

See **`nl_to_sql_finetune.ipynb`** for the full pipeline: training data, JSONL export, OpenAI fine-tuning job, and inference.
