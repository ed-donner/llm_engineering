---
title: Multimodal AI Synthetic Data Generator
emoji: 🎭
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
license: mit
---

# 🎭 Multimodal AI Synthetic Data Generator

Generate realistic synthetic datasets using multiple AI models via OpenRouter.

## ✨ Features

| Feature                | Description                                                                                   |
| ---------------------- | --------------------------------------------------------------------------------------------- |
| 🤖 **Multiple Models** | OpenAI GPT-4o Mini, Gemini 1.5 Flash, Claude 3 Haiku, Mistral, Llama, DeepSeek, Qwen          |
| 📊 **5 Dataset Types** | Customer Records, Financial Transactions, Tax Records, Healthcare Patients, E-commerce Orders |
| 🔄 **Robust JSON**     | Automatic extraction from model responses with error recovery                                 |
| 📥 **CSV Export**      | Download generated data for immediate use                                                     |
| 🎨 **Clean UI**        | Intuitive Gradio interface with live preview                                                  |

## 🚀 Quick Start

### Local Setup

```bash
# Clone the repository
git clone https://github.com/yaqubadesola/Multimodal-AI-Synthetic-Data-Generator-
cd Multimodal-AI-Synthetic-Data-Generator-

# Install dependencies
pip install -r requirements.txt

# Create .env file with your OpenRouter API key
echo "OPENROUTER_API_KEY=your_key_here" > .env

# Run the app
python app.py
```

### Render Deployment

1. Push your code to GitHub (already done).
2. Go to [Render.com](https://render.com/) and create a new Web Service.
3. Connect your GitHub repository (`yaqubadesola/Multimodal-AI-Synthetic-Data-Generator-`).
4. Set the start command to `python app.py`.
5. Add your `OPENROUTER_API_KEY` as an environment variable in Render settings.
6. Choose a Python environment and build settings as needed.
7. Deploy! Your Gradio app will be available at your Render URL.

---

## Key Features

### Synthetic Data Engine

- Generate realistic synthetic datasets for ML, analytics, and education
- Supports multiple dataset types: Customer Records, Financial Transactions, Tax Records, Healthcare Patients, E-commerce Orders
- Dynamic prompt engineering for diverse, high-fidelity data
- Robust JSON extraction and error handling
- Download generated data as CSV
- Configurable record count (5–50)

### Multimodal AI Model Support

- Choose from top models: OpenAI GPT-4o Mini, Gemini Flash, Grok Beta, Claude Haiku, DeepSeek V3
- Easily switch models for benchmarking and experimentation

### Gradio Web UI

- Intuitive, responsive interface for dataset generation
- Model and dataset selection via dropdowns
- Live data preview and CSV download
- User-friendly controls and instructions

### API & Integration

- REST endpoint for programmatic data generation
- Easy integration with ML pipelines, notebooks, and external apps

### Infrastructure & Deployment

- Zero-maintenance deployment on Render Web Service
- Environment variable support for API keys
- GitHub-based CI/CD for automated updates

---

For more details, see Render documentation.
