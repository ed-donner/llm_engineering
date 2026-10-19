# 🛍️ CSV Sales Q&A Assistant

### 🤖 An AI-powered sales assistant built with Python, Gradio, SQLite, and LLMs.

Ask questions about sales data, retrieve database records through AI tool calling, and optionally generate product images—all through an interactive chat interface.

Developed as an additional **Week 2 Community Contribution** for the AI Engineering course.

---

## ✨ Features

- 💬 **Interactive Chat UI** — Ask questions through a Gradio interface.
- 🧠 **Multiple AI Models** — Switch between OpenAI GPT and models available through OpenRouter.
- ⚡ **Streaming Responses** — See answers as they are generated.
- 🔍 **AI Tool Calling** — Search sales records and calculate total sales using Python database functions.
- 🗄️ **SQLite Database** — Query structured sales data loaded from a CSV file.
- 🖼️ **Optional Image Generation** — Choose whether to generate a product image with your answer.
- 🎙️ **Voice Input** — Speak your questions and convert them into text.
- 💡 **Example Questions** — Try predefined prompts to explore the assistant.

## ⚙️ How It Works

1. 💬 The user asks a question by typing or using the microphone.
2. 🧠 The selected AI model processes the question.
3. 🔧 When sales information is needed, the model can call the appropriate Python tool.
4. 🗄️ The tool queries the SQLite database and returns the results.
5. ✅ The AI generates a response, with optional product image generation.

## 📁 Project Structure

```text
CSV_Sales_Assistant/
├── CSV Sales Assistant.ipynb
├── synthetic_sales_dataset.csv
└── README.md
```

The notebook contains the application code, while the CSV provides the sample data used to create the local `sales.db` database.

## 📊 Dataset

This project uses a **synthetic sales dataset** created for educational and demonstration purposes.

It includes:

`Invoice Date` · `Product` · `Region` · `Retailer` · `Sales Method` · `State` · `Price per Unit` · `Total Sales` · `Units Sold`

The dataset is fictional and does not represent actual Nike sales. The existing database tools expect these column names and a compatible data structure.

## 🚀 Getting Started

1. 📥 Clone or download the repository containing this contribution.
2. 🐍 Open `CSV Sales Assistant.ipynb` in VS Code or Jupyter Notebook.
3. 📦 Install the Python dependencies required by the notebook.
4. 🔑 Configure your own OpenAI and/or OpenRouter API keys using the environment variables expected by the code.
5. ▶️ Run the notebook cells from top to bottom.

The notebook loads the CSV into SQLite and launches the Gradio interface in your browser.

## 💡 Example Questions

- What is revenue?
- What were the total sales of Men's Street Footwear in New York?
- Which state had the highest total sales for Women's Apparel sold online?

*The available tools retrieve matching sales records and calculate specified totals. Questions requiring rankings or aggregations may need the model to analyze the returned records.*

## 🔐 Important Notes

- 🔑 Never upload API keys or your `.env` file to GitHub.
- 💳 OpenAI and OpenRouter usage may incur API costs.
- 🧪 The included dataset is synthetic and intended for testing, not real-world financial analysis.
- 💻 GitHub stores the code; users run the application locally on their own computers.
- 🧩 Tool-calling behavior depends on the selected AI model.

---

### 🎯 Project Goal

Demonstrate how AI models can interact with structured data through Python tools, database queries, and an interactive interface.

**Built for learning, experimentation, and practical AI engineering.** 🚀

