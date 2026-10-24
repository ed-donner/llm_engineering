# 🛍️ CSV Sales Q&A Assistant

### 🤖 An AI-powered sales assistant built with Python, Gradio, SQLite, and LLMs.

This project was developed as a **Week 2 Community Contribution** for the AI Engineering course. It demonstrates how AI models can interact with a sales database through tool calling.

## ✨ Features

- 💬 **Interactive Gradio Interface** — Ask questions through a browser-based chat.
- 🧠 **Multiple AI Models** — Switch between OpenAI GPT and models available through OpenRouter.
- ⚡ **Streaming Responses** — Display answers as they are generated.
- 🔍 **Database Tool Calling** — Search sales records and calculate total sales.
- 🗄️ **SQLite Database** — Query sales data loaded from a CSV file.
- 🖼️ **Optional Image Generation** — Choose whether to generate product images.
- 🎙️ **Voice Input** — Transcribe spoken questions into text.

## ⚙️ How It Works

1. Ask a question using text or voice input.
2. The selected AI model processes the question.
3. For sales-related questions, the model can call Python database tools.
4. The tools query SQLite and return matching results.
5. The AI generates a response and can optionally generate a product image.

## 📁 Project Structure

```text
paziyax_week2_exercise/
├── README.md
├── sales_assistant.ipynb
└── synthetic_sales_dataset.csv
```

The notebook contains the application code, and the CSV supplies the sample data used to create the local `sales.db` database.

## 📊 Dataset

The project uses synthetic sales data for educational purposes.

**Columns:** `Invoice Date`, `Product`, `Region`, `Retailer`, `Sales Method`, `State`, `Price per Unit`, `Total Sales`, and `Units Sold`.

The dataset is fictional and does not represent actual Nike sales. The database tools expect these column names and a compatible data structure.

## 🚀 Getting Started

1. Clone or download the course repository.
2. Open `sales_assistant.ipynb` in VS Code or Jupyter Notebook.
3. Install the Python dependencies required by the notebook.
4. Configure your own OpenAI and/or OpenRouter API keys using the environment variables expected by the code.
5. Run the notebook cells from top to bottom to launch the Gradio interface.

The notebook loads the CSV into SQLite and launches the application.

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

