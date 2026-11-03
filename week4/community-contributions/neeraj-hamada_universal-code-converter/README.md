# 🌐 Universal Code Converter (Week 4 Community Contribution)

This repository contains a community contribution extending the **Code Generator** exercise from Week 4 of Ed Donner's LLM Engineering course. 

This project transforms the original Python-to-C++ script into a fully interactive **Universal Code Converter** wrapped in a modern, single-page Gradio interface, powered by Google's Gemini API.

## 📁 What's Included

* `universal-code-converter.ipynb`: The complete, self-contained Jupyter Notebook containing the Gradio UI, CSS styling, and LLM integration logic.

## 🚀 Features

* **Multi-Language Support:** Translates code between Python, C++, JavaScript, and TypeScript (easily expandable in the `LANG_MAP`).
* **Powered by Gemini:** Utilizes the `gemini-3.1-flash-lite` model for high-speed, idiomatic code generation.
* **Smart UI & Optimization:**
  * **Dynamic Dropdowns:** Selecting an input language automatically removes it from the output choices, preventing redundant conversions.
  * **Zero-Waste API Calls:** Backend checks prevent the Gemini API from firing if the input and output languages match.
  * **Robust Code Extraction:** Uses advanced regex parsing (`re.search` with `re.DOTALL`) to safely extract raw code and strip away conversational padding from the LLM.
  * **Responsive Design:** Custom CSS forces the code editors to fill the screen properly without redundant double-scrollbars.

## 🛠️ Setup & Execution

Since this notebook is designed to live inside the main course repository, it relies on the existing project setup.

1. Ensure your Python environment is active and dependencies (`gradio`, `openai`, `python-dotenv`) are installed.
2. Verify you have a `.env` file set up in the root directory with your Google API Key:
   ```env
   GOOGLE_API_KEY="your_gemini_api_key_here"
   ```
   
    ### 🔑 Getting Google API Key
     - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
     - Sign in with Google account
     - Create an API key

3. Open `universal-code-converter.ipynb` in your preferred Jupyter environment (VS Code, JupyterLab, etc.).
4. Run all the cells in order.
5. The Gradio interface will launch at the bottom of the notebook. Click the provided local URL (e.g., `http://127.0.0.1:7860`) to open it in a full browser tab for the best experience.

## 📧 Contact

For questions or suggestions, please open an issue on [GitHub](https://github.com/neerajhamada).