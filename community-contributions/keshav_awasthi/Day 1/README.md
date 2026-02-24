# High-Level Truth Advisor

This project is a Jupyter Notebook-based tool designed to act as a **brutally honest, high-level advisor and mirror**. It leverages the power of Large Language Models (LLMs) via the Groq API to provide unfiltered, rational, and strategically deep feedback on various life and professional situations.

## 🚀 Overview

The **High-Level Truth Advisor** is designed to challenge your thinking, expose blind spots, and offer a prioritized plan for improvement. Instead of providing comfort, it focuses on the "harsh truth" needed for genuine growth.

### Key Features
- **Brutally Honest Feedback:** No softening of truths or flattery.
- **Deep Strategic Analysis:** Looks at situations with objectivity and strategic depth.
- **Actionable Plans:** Provides a precise, prioritized plan for mindset and action changes.
- **Seamless Integration:** Uses Groq's high-speed API with Llama 3 models.

## 🛠️ Setup

1. **Environment Variables:**
   Create a `.env` file in the same directory and add your Groq API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

2. **Dependencies:**
   Ensure you have the following packages installed:
   ```bash
   pip install openai python-dotenv ipython
   ```

3. **Run the Notebook:**
   Open `Harsh_truth.ipynb` in your preferred Jupyter environment (VS Code, JupyterLab, etc.) and run the cells.

## 🧠 How It Works

The advisor uses a specialized **System Prompt** that instructs the AI to:
- Act as a mirror and challenge assumptions.
- Point out self-deception or wasted time.
- Avoid validation and flattery.
- Provide a prioritized plan for the next level of growth.

### Example Query
> "Is it good that I have worked in 3 different domain of Projects and still I don't have indepth knowledge of any domain?"

The AI analyzes the pros (broad perspective, adaptability) and cons (lack of expertise, limited career progression) objectively and provides a roadmap for specialization.

## 📂 Project Structure
- `Harsh_truth.ipynb`: The main notebook containing the logic and prompts.
- `.env`: (User-created) Stores the API credentials.

---
*Created by Keshav Awasthi as part of the community contributions.*
