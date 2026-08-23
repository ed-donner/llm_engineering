# Requirements and Dependencies 📋

This document outlines the detailed system, library, and environment requirements for the **AI Tutor** project.

## 1. System Requirements
- **Python:** Version `3.12+` is recommended (tested with Python `3.12.x`).
- **Package Manager:** [uv](https://github.com/astral-sh/uv) (strongly recommended for extremely fast installs and isolated runtimes).

---

## 2. Python Package Dependencies
The project relies on the following libraries (listed in [requirements.txt](file:///d:/Projects/llm_engineering/community-contributions/Arjav014/AI-tutor/requirements.txt)):

| Package | Purpose |
| :--- | :--- |
| `openai` | Accesses the OpenAI-compatible Gemini API endpoints. |
| `python-dotenv` | Loads environment variables (like API keys) from a local `.env` file. |
| `ipython` | Enables rich content rendering in the Jupyter notebook (e.g., using `Markdown`, `display`, and `update_display` functions). |
| `ipykernel` | Connects Jupyter interfaces (like Notebook or Lab) to the Python kernel. |
| `jupyter` | The notebook server interface for creating and running notebooks. |

---

## 3. Environment Variables & API Access
To access the underlying language model (`gemini-2.5-flash-lite`), you need a Gemini API Key.

1. **Get a Key:** Create a free API key at [Google AI Studio](https://aistudio.google.com/).
2. **File Configuration:** Create a file named `.env` in the same directory as the notebook:
   ```env
   GOOGLE_API_KEY=your_actual_api_key_here
   ```
3. **Usage in Code:** The notebook uses `python-dotenv` to locate and load this key dynamically:
   ```python
   load_dotenv(override=True)
   api_key = os.getenv('GOOGLE_API_KEY')
   ```

---

## 4. Run Environment Verification
When starting the notebook, verify that:
- Your API key is valid.
- Internet connectivity is active (to connect to `generativelanguage.googleapis.com`).
- The Python virtual environment is loaded and active.
