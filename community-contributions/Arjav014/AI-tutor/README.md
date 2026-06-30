# AI Tutor 🤖📚

An interactive, educational, and humorous AI Tutor implemented in a Jupyter Notebook. It uses the Gemini API (via the OpenAI Python client) to answer programming, computer science, mathematics, and software engineering questions with engaging explanations, analogies, and light jokes.

## Features
- **Engaging AI Persona:** Explains complex technical topics clearly, using humor, analogies, and relatable examples.
- **Markdown-formatted Outputs:** Delivers explanations with structured headings, bullet points, formatted code blocks, and tables.
- **Real-time Streaming:** Streams responses chunk-by-chunk to keep the learning experience interactive and fast.
- **OpenAI Client Integration:** Integrates Gemini's OpenAI-compatible endpoint using the standard `openai` library.

---

## Prerequisites
- **Python 3.12+**
- **Gemini API Key:** Obtain one from [Google AI Studio](https://aistudio.google.com/).
- **uv:** A fast Python package installer and resolver.

---

## Setup Instructions

### 1. Clone & Navigate
Navigate to the project directory:
```bash
cd community-contributions/Arjav014/AI-tutor
```

### 2. Configure Environment Variables
Create a `.env` file in the root of the `AI-tutor` directory:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

---

## Running with `uv` ⚡

[uv](https://github.com/astral-sh/uv) is a fast replacement for `pip`, `pip-tools`, and virtual environment management. Here are three ways to run this notebook using `uv`:

### Method 1: Running Jupyter Directly (Zero Setup)
`uv` can run commands in ephemeral environments, installing packages on the fly. You don't even need to create a virtual environment manually:
```bash
uv run --with jupyter -r requirements.txt jupyter notebook main.ipynb
```

### Method 2: Standard Virtual Environment Flow
If you prefer a persistent virtual environment:

1. **Create and activate the virtual environment:**
   ```bash
   # Create a virtual environment
   uv venv

   # Activate the environment
   # On Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Start the Jupyter Notebook server:**
   ```bash
   jupyter notebook main.ipynb
   ```

---

## Project Structure
- [main.ipynb](file:///d:/Projects/llm_engineering/community-contributions/Arjav014/AI-tutor/main.ipynb): The main interactive Jupyter Notebook.
- [requirements.txt](file:///d:/Projects/llm_engineering/community-contributions/Arjav014/AI-tutor/requirements.txt): Python dependencies.
- [requirements.md](file:///d:/Projects/llm_engineering/community-contributions/Arjav014/AI-tutor/requirements.md): Detailed explanation of dependencies and environment requirements.
