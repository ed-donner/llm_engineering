# 🧠 Code Quiz Tutor

An active-recall quiz tool that takes any code snippet, generates a 5-question quiz, then grades your answers and tells you what to improve.

---

## How it works

This notebook runs in **two phases:**

**Phase 1 — Quiz Generator**

Paste a code snippet → get 5 questions across four types:

- Output tracing
- Bug finding
- Conceptual / logic
- Refactor / improvement

**Phase 2 — Grader & Tutor**

Paste your answers → get a score, per-question feedback, and targeted next steps.

---

## Requirements

Install the OpenAI Python library before running:

pip install openai

Set your API key as an environment variable:

export OPENAI_API_KEY="your-key-here"

Or paste it directly in the config cell (not recommended for shared notebooks).

---

## How to use

### Step 1 — Paste your code

In the **Phase 1 cell**, replace the placeholder inside `user_code` with your code snippet. Any language is supported — Python, JavaScript, TypeScript, Java, SQL, etc.

user_code = """

paste your code here

"""

Run the cell. Your 5 questions will be printed below.

---

### Step 2 — Answer the questions

Read the questions carefully.

Write your 5 answers in the **Answers cell**:

user_answers = """

1. Your answer to Q1
2. Your answer to Q2
3. Your answer to Q3
4. Your answer to Q4
5. Your answer to Q5

"""

---

### Step 3 — Get graded

Run the **Phase 2 cell**. The grader will:

- Mark each answer as Correct ✅, Partially correct 🟡, or Incorrect ❌
- Explain what you got right and wrong
- Give you a score out of 5
- Suggest what to study next

---

## Notes

- Phase 2 automatically passes the original code and the Phase 1 quiz to the grader — you don't need to copy anything between cells.
- If you get a bad quiz (e.g. a hallucinated bug), re-run Phase 1. LLMs occasionally make mistakes.
- For best results, use focused snippets (1 function or 1 module at a time) rather than entire files.
