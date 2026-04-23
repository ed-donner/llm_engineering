# 🔍 Multi-LLM Debugger

A multi-agent AI debugging system that uses three specialized LLM agents — powered by **Google Gemini** and **Groq** — to collaboratively analyze, debug, and fix your code.

## How It Works

When you submit a code snippet and an error message, three agents engage in a structured discussion:

| Agent | Model | Role |
|---|---|---|
| 🔍 **Debugger** | Gemini (via Google API) | Identifies root causes, strict and technical |
| 💡 **Creative Solver** | Groq (gpt-oss-20b) | Proposes alternative fixes, challenges assumptions |
| 📝 **Docs Expert** | Groq (gpt-oss-20b) | Asks clarifying questions, writes final summary & corrected code |

The agents talk to each other (not to you) across multiple rounds, then wrap up with a final summary and corrected code from the Docs Expert.

## Setup

### 1. Clone & navigate
```bash
git clone <your-repo-url>
cd LLM-Projects
```

### 2. Create and activate virtual environment
```bash
uv venv
.venv\Scripts\activate   # Windows
```

### 3. Install dependencies
```bash
uv pip install -r requirements.txt
```

### 4. Add your API keys
Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_google_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

- Get a Google API key at [aistudio.google.com](https://aistudio.google.com)
- Get a Groq API key at [console.groq.com](https://console.groq.com)

### 5. Select the kernel
In VS Code, open `multi-llm-debugger.ipynb` and select the `.venv` kernel from the kernel picker.

## Usage

At the bottom of the notebook, call `run_debug_session` with your buggy code and error:

```python
code_snippet = """
def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)

result = calculate_average([])
print(result)
"""

error_message = "ZeroDivisionError: division by zero"
run_debug_session(code_snippet=code_snippet, error_message=error_message)
```

The agents will debate for a configurable number of rounds, then the Docs Expert produces a final summary and corrected code.

## Requirements

```
python-dotenv
openai
requests
ipython
```

## Project Structure

```
LLM-Projects/
├── .env                      # API keys (not committed)
├── .venv/                    # Virtual environment
├── multi-llm-debugger.ipynb  # Main notebook
├── requirements.txt
├── pyproject.toml
└── README.md
```