# Resume Role Prediction with Fine-Tuned GPT 4.1-nano

This project demonstrates how to fine-tune a GPT model to predict job roles from synthetic resume summaries. The workflow is divided into clear steps:

## Project Overview

We leverage a curated dataset of synthetic resume summaries and corresponding job roles to train a GPT-based model. The goal is to have the model predict the job role given a resume summary, which can be tested interactively via a Gradio interface.

## Steps

1. **Data Curation**
  - Load the synthetic dataset from Hugging Face.
  - Convert it into a Pandas DataFrame for easier manipulation.
  - Select subsets for fine-tuning and validation.
2. **Data Preparation for Fine-Tuning**
  - Convert the DataFrame into JSONL format suitable for OpenAI fine-tuning.
  - Ensure each training example clearly separates the prompt (resume summary) from the completion (job role).
3. **Fine-Tuning the Model**
  - Upload the JSONL training and validation files to OpenAI.
  - Fine-tune a GPT-4.1-nano  
  - Monitor the fine-tuning job until completion.
4. **Model Evaluation**
  - Test the fine-tuned model on unseen summaries.
  - Calculate accuracy and  visualize predictions.
  - Ensure the model outputs only the job role, not the full summary.
5. **Interactive Interface**
  - Deploy a Gradio interface for real-time role prediction.
 

## Notes

- Fine-tuning requires clean, short completions (only the role) to prevent the model from echoing the input.
- Small datasets may lead to overfitting; consider increasing training examples for better generalization.
- This pipeline can be extended for other resume-related tasks or NLP classification tasks.

