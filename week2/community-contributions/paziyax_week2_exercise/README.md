# 🛍️ Sales Q&A Assistant

### 🤖 An AI-powered sales assistant built with Python, Gradio, SQLite, and LLMs.

This project was developed as a **Week 2 Community Contribution** for the AI Engineering course. It demonstrates how AI models can interact with a sales database through tool calling.

## ✨ Features

- 💬 **Interactive Gradio Interface** — Ask questions through a browser-based chat.
- 🧠 **Multiple AI Models** — Switch between OpenAI GPT and models available through OpenRouter.
- ⚡ **Streaming Responses** — Display answers as they are generated.
- 🔍 **Database Tool Calling** — Search sales records and calculate total sales.
- 🗄️ **SQLite Database** — Generate synthetic sales data in Python and load it into a local SQLite database.
- 🖼️ **Optional Image Generation** — Choose whether to generate product images.
- 🎙️ **Voice Input** — Transcribe spoken questions into text.

## ⚙️ How It Works

1. Python generates synthetic sales records when the notebook runs.
2. The generated records are loaded into the local `sales.db` SQLite database.
3. Ask a question using text or voice input in the Gradio interface.
4. The selected AI model processes the question and can call Python database tools for sales-related questions.
5. The tools query SQLite and return results to the AI model.
6. The AI generates a response and can optionally generate a product image.

## 📁 Project Structure

```text
paziyax_week2_exercise/
├── README.md
└── sales_assistant.ipynb
```

The notebook contains the application code and synthetic-data generator. When the notebook runs, it creates the local `sales.db` database. The CSV dataset is not required, and the generated database does not need to be committed to GitHub.

## 📊 Dataset

The project generates fictional sales data for educational purposes.

**Columns:** `Invoice Date`, `Product`, `Region`, `Retailer`, `Sales Method`, `State`, `Price per Unit`, `Total Sales`, and `Units Sold`.

The number of generated records can be changed using the `NUM_RECORDS` variable in the notebook.

The dataset is fictional and does not represent actual Nike sales. The database tools expect these column names and a compatible data structure.

## 🚀 Getting Started

1. Clone or download the course repository.
2. Open `sales_assistant.ipynb` in VS Code or Jupyter Notebook.
3. Install the Python dependencies required by the notebook.
4. Configure your own OpenAI and/or OpenRouter API keys using the environment variables expected by the code.
5. Run the notebook cells from top to bottom to generate the synthetic data, create the local SQLite database, and launch the Gradio interface.

The notebook generates the sample data and loads it into SQLite, so you do not need to download a separate CSV file.

## 💡 Example Questions

- What is revenue?
- What were the total sales of Men's Street Footwear in New York?
- Which state had the highest total sales for Women's Apparel sold online?

## 🔐 Important Notes

- Never upload API keys or your `.env` file to GitHub.
- OpenAI and OpenRouter usage may incur API costs.
- The dataset is synthetic and intended for demonstration, not real-world financial analysis.
- Tool-calling behavior depends on the selected AI model.

---

**Built for learning, experimentation, and practical AI engineering.** 🚀

