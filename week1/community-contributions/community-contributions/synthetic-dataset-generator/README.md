# LLM-Powered Dataset Synthesizer: LLaMA 3 + Gradio Demo

This interactive demo showcases a synthetic dataset generation pipeline powered by Meta's LLaMA 3.1 8B-Instruct model, running in 4-bit quantized mode. Users can input natural language prompts describing the structure and logic of a desired dataset, and the model will generate tabular data accordingly.

## ✨ Description

Modern LLMs are capable of reasoning over structured data formats and generating realistic, constrained datasets. This demo leverages the LLaMA 3.1 instruct model, combined with prompt engineering, to generate high-quality synthetic tabular data from plain-language descriptions.

Key components:
- **LLaMA 3.1 8B-Instruct** via Hugging Face Transformers
- **4-bit quantized loading** with `bitsandbytes` for memory efficiency
- **Custom prompt framework** for schema + value constraints
- **Interactive interface** built with Gradio for user-friendly data generation

## 🚀 Functionality

With this tool, you can:
- Generate synthetic datasets by describing the column names, data types, value logic, and number of rows
- Apply constraints based on age, gender, matching conditions, and more (e.g., “females over 40; males under 40”)
- Preview the raw model output or extract structured JSON/tabular results
- Interactively explore and copy generated datasets from the Gradio UI

## 🛠️ Under the Hood

- The model prompt template includes both a **system message** and user instruction
- Output is parsed to extract valid JSON objects
- The generated data is displayed in the Gradio interface and downloadable as CSV

## 📦 Requirements

- Python (Colab recommended)
- `transformers`, `bitsandbytes`, `accelerate`, `gradio`, `torch`
- Hugging Face access token with permission to load LLaMA 3.1

---

Ready to generate smart synthetic datasets with just a sentence? Try it!
