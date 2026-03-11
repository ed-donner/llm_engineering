# Price Band Classification Fine-tuning (Week 6)

## Overview
This project demonstrates fine-tuning a language model (OpenAI GPT-3.5-turbo) to classify products into price bands (budget, midrange, premium) based on product descriptions and price data.

## Features
- Data loading and exploratory price distribution analysis
- Price bin creation and class balance visualization
- Fine-tuning dataset construction and export (JSONL)
- File upload and job creation/monitoring with OpenAI API
- Inference with fine-tuned model
- Evaluation: accuracy, F1, classification report, confusion matrix, per-class F1 visualization

## Setup
1. Clone the repository and navigate to the project folder.
2. Install dependencies:
   - Python 3.8+
   - `pip install openai pandas numpy matplotlib seaborn scikit-learn python-dotenv`
3. Set your OpenAI API key in a `.env` file:
   ```
   OPENAI_API_KEY=your-key-here
   ```

## Usage
- Open the notebook `price_band_classification.ipynb`.
- Follow the workflow steps:
  1. Load your dataset (CSV/XLSX)
  2. Create price bins
  3. Visualize price distribution and class balance
  4. Prepare fine-tuning dataset (JSONL)
  5. Upload file to OpenAI
  6. Create and monitor fine-tuning job
  7. Run inference with fine-tuned model
  8. Evaluate classification performance

## Limitations
- Requires OpenAI API access and sufficient quota for fine-tuning jobs.
- Dataset must include price and product description columns.
- Price bin thresholds may need adjustment for your dataset.

## Conclusion
This notebook provides a modular workflow for price band classification using LLM fine-tuning. Utility functions are provided for each step. Adapt column names, file paths, and model names as needed for your use case.

## Limitations
- Only .md and .txt files supported
- Relies on LLM quality for chunking and QA
- Requires OpenAI API key

## Conclusion
This notebook provides a robust, modular workflow for building a personal knowledge worker with conversational RAG capabilities.
