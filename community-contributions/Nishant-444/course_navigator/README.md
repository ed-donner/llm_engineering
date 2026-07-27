# Course Navigator & RAG Assistant

A community contribution by **Nishant Sharma**.

The **Course Navigator & RAG Assistant** is a self-contained RAG (Retrieval-Augmented Generation) system built to help students search, navigate, and chat with all materials in the **LLM Engineering** course.

It parses and indexes all official weekly notebooks (`week1` through `week8`), Python scripts, and technical guides. By using local semantic embeddings and a vector database, it enables you to ask curriculum-based questions and get instant, accurate answers with direct file citations.

---

## ✨ Features

- **Local Semantic Search**: Generates 384-dimensional text embeddings locally and for free using `sentence-transformers/all-MiniLM-L6-v2`. Computes cosine similarities using `numpy` to retrieve the most relevant sections instantly.
- **Contextual AI Answers**: Feeds relevant codebase sections into a custom system prompt and queries OpenRouter (`google/gemini-2.5-flash`) using your environment credentials.
- **Low-Cost API Optimization**: Restricts response tokens to stay well within low-budget limits.
- **Premium Gradio Web Interface**: Includes a responsive dark-mode chat and explore dashboard.
- **Jupyter Notebook Demo**: Includes a step-by-step notebook demonstrating RAG operations programmatically.

---

## 📁 Directory Structure

```
course_navigator/
├── indexer.py              # Crawls the workspace, parses cells/code, and builds the embedding index
├── searcher.py             # Computes query similarities and synthesizes answers via OpenRouter
├── app.py                  # Runs the responsive Gradio web interface (chat, search, status controls)
├── course_navigator.ipynb  # Interactive Jupyter notebook walkthrough
├── navigator_index.pkl     # Serialized vector database containing chunk content and embeddings (generated)
└── README.md               # Documentation and setup guide (this file)
```

---

## 🚀 Quick Start Guide

### 1. Setup Dependencies
Ensure you are using the virtual environment `.venv` from the root of the project. If you have not done so, run setup.
If you need to install the dependencies manually:
```bash
pip install sentence-transformers gradio openai python-dotenv numpy
```

### 2. Build the Search Index
Run the indexer script to parse the repository and generate the vector embeddings. It will scan all guides and weeks (automatically skipping hidden files, `.venv`, and other student submissions):
```bash
python indexer.py
```
*(This process downloads a small ~120MB local embedding model on the first run and takes about 1-2 minutes to encode all text chunks).*

### 3. Launch the Web Interface
Start the interactive Gradio web application:
```bash
python app.py
```
Open your browser and navigate to the local link printed in the terminal (usually `http://127.0.0.1:7860`).

### 4. Interactive Notebook Walkthrough
Alternatively, you can open and run `course_navigator.ipynb` inside Cursor/VSCode to inspect the search scores and response payloads programmatically.

---

## 🛠️ Configuration Note
This project reads your API settings from the `.env` file in the root of the workspace. Make sure `OPENROUTER_API_KEY` (or `OPENAI_API_KEY` holding an OpenRouter token) is configured.
