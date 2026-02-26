# Technical Question Explainer — What This Notebook Does

This document explains the notebook in plain language so anyone can understand what each part is for and why it’s there.

---

## The Big Picture: What Is This For?

Imagine you have a **technical tutor** that can answer questions about code, software, data, and AI. You type (or paste) a question, and the tutor writes back an explanation.

This notebook is that tutor. It uses two different “tutors” (AI services):

1. **OpenAI** — a tutor that runs on the internet (you need an API key).
2. **Ollama** — a tutor that runs on your own computer (no internet needed after setup).

You can ask one question and get answers from both, and the answers appear **as they’re being written** (streaming), like someone typing in real time.

---

## What You Need Before You Start

- A **Jupyter notebook** (or similar) to run the cells.
- An **OpenAI API key** in a `.env` file (only if you want to use the online tutor).
- **Ollama** installed with a model (e.g. `llama3.2`) if you want the local tutor.

---

## Section 1: Bringing In the Tools (Imports)

**What you see:**  
A block that starts with `import os`, `from openai import OpenAI`, etc.

**What it means in simple terms:**  
Before you can use a feature in Python, you have to “bring it in.” This cell brings in:

- **os** — so we can read things from your computer’s environment (like your secret API key).
- **json** — for working with data in a standard text format.
- **OpenAI** — the official way to talk to OpenAI’s AI from code.
- **dotenv** — so we can load your API key from a `.env` file instead of putting it in the notebook.
- **Markdown, display, update_display** — so we can show nicely formatted text (headings, lists) and update it live as the AI types.
- **ollama** — the way we talk to the AI running on your machine (Ollama).

**Why it’s here:**  
Without these “imports,” the rest of the notebook wouldn’t know how to call OpenAI, Ollama, or display streaming text.

---

## Section 2: Choosing Which “Tutors” to Use (Model Names)

**What you see:**  
Two lines like:

- `MODEL_GPT = 'gpt-5.1-mini'`
- `MODEL_OLLAMA = 'llama3.2'`

**What it means in simple terms:**  
These are just **names** we give to the two AIs we’ll use:

- **MODEL_GPT** — the name of the OpenAI model (the “online tutor”). You can change this to another OpenAI model name if you want.
- **MODEL_OLLAMA** — the name of the Ollama model (the “local tutor”), e.g. the one you installed with Ollama.

**Why it’s here:**  
So later we can say “use this model” in one place. If we want to switch models, we only change these two lines.

---

## Section 3: Checking Your Secret Key (Environment & API Key)

**What you see:**  
Code that calls `load_dotenv`, gets `OPENAI_API_KEY`, and then prints “API key looks good so far” or “API key is not valid.”

**What it means in simple terms:**

- **load_dotenv(override=True)** — “Read the `.env` file in this folder and load any secrets (like the API key) into the environment.” That way the key isn’t written in the notebook.
- **api_key = os.getenv('OPENAI_API_KEY')** — “Get the OpenAI API key from the environment.”
- The **if/else** — a simple check: “Does the key exist, start with `sk-proj-`, and have more than 10 characters?” If yes, we print that it looks good; if not, we say it’s not valid.

**Why it’s here:**  
So you know right away whether the notebook can talk to OpenAI. If the key is missing or wrong, you’ll see the message and can fix the `.env` file before running the rest.

---

## Section 4: Your Question — Typed or Pre-Written (Input vs Hardcoded)

**What you see:**  
A variable `USE_INPUT`, a block of text called `DEFAULT_QUESTION`, and some `if/else` logic that either asks you to type a question or uses the default.

**What it means in simple terms:**

- **USE_INPUT = False** — “Don’t ask me to type; use the pre-written question.”
  - Set it to **True** if you want to type (or paste) your own question each time you run the cell.
- **DEFAULT_QUESTION** — The pre-written question we use when you don’t type one (e.g. “Explain this code: yield from …”).
- **if USE_INPUT:** … **else:** …  
  - If `USE_INPUT` is True: the program asks you to enter a question; if you just press Enter, it uses the default.
  - If `USE_INPUT` is False: it always uses the default question and doesn’t ask you.
- **system_prompt** — Instructions we give the AI once: “You are a helpful technical tutor who answers questions about …”
- **user_prompt** — The actual question we send: “Please give a detailed explanation to the following question: ” plus your question.
- **messages** — A list of two messages: one “system” (the tutor’s role) and one “user” (your question). Both OpenAI and Ollama expect this kind of list.

**Why it’s here:**  
So you can either try the notebook quickly with a fixed example (hardcoded) or use it as a real tool by typing your own questions (input). One notebook, two ways to use it.

---

## Section 5: Getting the Answer from OpenAI (Streaming)

**What you see:**  
Code that creates an `OpenAI()` client, calls `chat.completions.create` with `stream=True`, and then a loop that adds each piece of text to `response` and updates the display.

**What it means in simple terms:**

- **client = OpenAI()** — “Create a connection to OpenAI using the API key from the environment.”
- **stream = client.chat.completions.create(...)** — “Send our messages to OpenAI and ask for an answer, but don’t wait for the whole answer — give it to us in small pieces (stream).”
- **response = ""** — We start with an empty answer and will glue the pieces together.
- **display_handle = display(Markdown(""), display_id=True)** — “Prepare a place in the notebook where we’ll show the answer, and remember that place so we can update it.”
- **for chunk in stream:** — “For each small piece of text that OpenAI sends back…”
  - **chunk.choices[0].delta.content** — “…get the new bit of text in that piece.”
  - **response += ...** — “…add it to our full answer.”
  - **update_display(Markdown(...), display_id=...)** — “…and refresh the displayed text so the user sees the answer growing in real time.”

**Why it’s here:**  
This is the “online tutor” part: it sends your question to OpenAI and shows the reply as it’s being generated (streaming), so you don’t have to wait for the entire answer before seeing something.

---

## Section 6: Getting the Answer from Ollama (Streaming)

**What you see:**  
Code that calls `ollama.chat(...)` with `stream=True` and a loop that takes each chunk, gets the text, and updates a second display.

**What it means in simple terms:**

- **ollama_response = ""** — We start with an empty string for the local model’s answer.
- **ollama_handle = display(Markdown(""), display_id=True)** — “Prepare another place in the notebook for the second tutor’s answer.”
- **for chunk in ollama.chat(..., stream=True):** — “Ask Ollama for an answer in small pieces, and for each piece…”
  - **chunk.get("message", {}).get("content", "")** — “…get the new bit of text from that piece (Ollama’s format is slightly different from OpenAI’s).”
  - **ollama_response += part** — “…add it to the full answer.”
  - **update_display(Markdown(...), ...)** — “…and refresh the display so the user sees the local tutor’s answer growing in real time.”

**Why it’s here:**  
This is the “local tutor” part: same question, but answered by the model running on your computer. You can compare the two answers and see how OpenAI and Ollama differ.

---

## Quick Reference: What Runs When

1. **Run Section 1** — Load tools (imports).
2. **Run Section 2** — Set model names.
3. **Run Section 3** — Load `.env` and check API key.
4. **Run Section 4** — Set your question (typed or default) and build the message list.
5. **Run Section 5** — Get streaming answer from OpenAI.
6. **Run Section 6** — Get streaming answer from Ollama (optional).

You can run Section 5 and 6 in any order; both use the same `messages` from Section 4.

---

## Summary in One Sentence

This notebook lets you ask a technical question (by typing it or using a built-in example), then shows you answers from both an online AI (OpenAI) and a local AI (Ollama), with the text appearing word-by-word as it’s generated.
