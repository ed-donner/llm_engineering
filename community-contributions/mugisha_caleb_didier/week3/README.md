# Kinyarwanda-English Phrasebook Generator

A synthetic data generator that creates bilingual phrasebook entries using open-source LLMs on Google Colab.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1sStoMCqo7XTKAVB4JhxEtWhcYn0GEbt2?usp=sharing)

## What it does

- Generates Kinyarwanda-English phrase pairs across 6 practical categories (greetings, market, travel, food, emergency, numbers)
- Each phrase includes a phonetic pronunciation guide and usage context
- Supports two open-source models: Llama 3.2 3B and Qwen 2.5 3B (switchable via Gradio UI)
- Exports results as a downloadable CSV

## Skills demonstrated

- Loading and running open-source models from HuggingFace
- 4-bit quantization with BitsAndBytesConfig
- Chat templates with `apply_chat_template()`
- GPU memory management (loading one model at a time)
- Gradio Blocks UI with interactive controls
- Structured synthetic data generation (JSON parsing from LLM output)

## How to run

1. Open the notebook in Google Colab (click the badge above)
2. Select a **T4 GPU** runtime (Runtime > Change runtime type)
3. Add your HuggingFace token to Colab Secrets (key: `HF_TOKEN`)
4. Run all cells

## Sample output

| Kinyarwanda | English | Pronunciation | Context |
|---|---|---|---|
| Muraho | Hello | moo-RAH-ho | General greeting, used any time of day |
| Murakoze | Thank you | moo-rah-KO-zeh | Expressing gratitude in any situation |
| Ni angahe? | How much is it? | nee ahn-GAH-heh | Asking the price at a market stall |
| Ndashaka kugura... | I want to buy... | ndah-SHAH-kah koo-GOO-rah | Starting a purchase at a shop or market |
