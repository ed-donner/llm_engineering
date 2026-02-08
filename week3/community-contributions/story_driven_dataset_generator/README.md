# 🎭 Story-Driven Synthetic Dataset Generator

A creative approach to generating interconnected, narrative-driven synthetic data using multiple AI models.

## Features

| Mode | Description |
|------|-------------|
| 📊 **Standard** | Classic row-by-row synthetic data generation |
| 📖 **Story Chain** | Chronologically connected narrative data (e.g., startup journey from founding → IPO) |
| 🥊 **Model Battle** | Two AI models compete on the same prompt, side-by-side comparison |
| 🔄 **Data Remix** | Paste sample data, AI generates more matching your style |
| ✏️ **Custom** | Define your own schema and requirements |

## Models Supported

- **OpenAI**: GPT-4o-mini, GPT-4o
- **Google Gemini**: Gemini 1.5 Flash, Gemini 2.0 Flash

## Style Personas

- 🏢 **Corporate Analyst** - Formal business terminology, precise numeric data
- 🎨 **Creative Writer** - Colorful names, imaginative patterns
- 🔬 **Data Scientist** - Statistical distributions, edge cases, ML-ready data

## Pre-built Domains

- 🚀 Startup Journey (founding → funding rounds → exit)
- 🛒 Customer Journey (first visit → loyal customer)
- 🏥 Patient Treatment (symptoms → diagnosis → recovery)
- 📈 Stock Performance (IPO → volatility → trends)
- 🎮 Game Player Progress (onboarding → mastery)

## Setup

1. Ensure you have API keys in your `.env` file:
   ```
   OPENAI_API_KEY=your_key_here
   GOOGLE_API_KEY=your_key_here
   ```

2. Install dependencies:
   ```bash
   pip install openai google-generativeai gradio pandas python-dotenv
   ```

3. Run the notebook cells in order, then launch the Gradio UI in the final cell.

## Usage

1. Select a **Model** (GPT-4o-mini recommended for speed)
2. Choose a **Domain** or use Custom
3. Pick a **Style Persona**
4. Set **Number of Records**
5. Click **Generate**!
