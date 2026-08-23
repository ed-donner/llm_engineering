# Flexor: Synthetic Dataset Generator

## Overview
Flexor lets users describe their desired dataset in plain English and instantly get structured, realistic data powered by open-source LLMs (LLaMA 3, Zephyr) via HuggingFace Inference API.

## Features
- Natural language dataset definition
- Optional column schema for precise field control
- Supports JSON and CSV export (up to 200 rows, generated in batches of 20)
- Clean Gradio UI
- Secure token loading from HF_TOKEN environment variable
- No user token input required

## Technical Details
- Single-file Gradio app (notebook or app.py)
- Uses HuggingFace chat_completion endpoint for instruct models
- Batch generation for large datasets
- JSON and CSV export

## Requirements
- Python packages: gradio, pandas, requests, python-dotenv
- HuggingFace account and HF_TOKEN set in environment

## Setup
1. Install dependencies:
   ```bash
   pip install gradio pandas requests python-dotenv
   ```
2. Set up HuggingFace token in `.env`:
   ```env
   HF_TOKEN=your_hf_token_here
   ```
3. Run the notebook or app

## Usage
- Enter a natural language description of your dataset
- Optionally specify column schema (comma-separated)
- Choose number of rows and model
- Click "Generate Dataset" to get JSON and CSV outputs

## Limitations
- Max 200 rows per dataset
- No image or advanced data types
- Relies on LLM quality for realism

## Conclusion
Flexor provides a fast, flexible way to generate synthetic datasets for prototyping, testing, and research using state-of-the-art open-source LLMs.
