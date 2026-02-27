# 🇳🇬 Nigerian Financial Advisor Prototype

## Week 2 Exercise: AI Bootcamp

This project is a functional prototype of a localized financial consultant. It integrates **Cloud-based LLMs** to provide data-driven advice on the Nigerian investment landscape, helping users navigate inflation and currency hedging.

---

## 🌟 Features

* **JSON-Driven:** All interest rates are fetched from `get_investment_rates` function. This ensures zero hallucination on critical financial figures and provides a "source of truth."
* **Hybrid Inference:** Users can seamlessly toggle between **GPT-4o** and **Claude Sonnet** via the UI.
* **Streaming Interface:** Implements real-time token generation, allowing the advisor's response to appear dynamically for a smoother user experience.
* **Inflation-Aware Logic:** The system prompt is engineered to force the advisor to consider the **2026 inflation rate** (approx. 27%+) when evaluating returns, providing "real" financial context.

---

## 🛠️ Technical Stack

| Component | Technology |
| :--- | :--- |
| **Framework** | [Gradio](https://gradio.app/) (UI) |
| **Language Models** | Open AI (GTP-4), Anthroptic (Claude Sonnet) & Google (Gemini) |
| **Architecture** | Agentic Tool-Use (Function Calling) |

---

## 📈 How to Use

1.  **Initialize Data:** Run the notebook cells to get_investment_rates.
2.  **Select Brain:** Use the Dropdown options in the Gradio UI to choose between models.
3.  **Ask Questions:** * *"What is the USD rate on Risevest?"*
    * *"Compare Piggyvest and Cowrywise rates."*
    * *"How can I beat inflation with 500k Naira?"*
4.  **Observe Tool Use:** Watch the logs or the advisor's response as it calls the JSON tool to provide accurate, non-hallucinated data.

---

> **Note:** This tool is designed for educational purposes as part of an AI Bootcamp. Always verify financial rates directly with the platforms (Piggyvest, Cowrywise, Risevest) before making investment decisions.