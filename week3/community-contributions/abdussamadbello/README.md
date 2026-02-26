## Week 3 – Llama 3.2 Instruct (Hugging Face) quizzes you and scores you (abdussamadbello)

You **select a list of topics** → **Llama 3.2 Instruct** (Hugging Face) **generates a quiz** → **you** answer each question → **Llama scores** your answers and gives feedback. No OpenAI; runs locally with **Hugging Face** `transformers` and **Llama 3.2 Instruct** (1B).

The notebook `week3-assignment.ipynb`:
- **TOPICS**: you choose (e.g. `["RAG", "prompts", "evaluation"]`).
- **generate_quiz(topics)**: Llama 3.2 returns a list of questions (JSON); parsed with a simple fallback if the model output is malformed.
- **You answer**: in interactive use you type each answer; in the demo we use sample answers so the notebook runs without typing.
- **score_answers(...)**: Llama scores each answer 1–5 and gives one-line feedback.
- **print_scores(...)**: prints per-question score and feedback, then total.

### Prerequisites

- **Gated model:** Accept the [Llama 3.2 license](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct) and run `huggingface-cli login`.
- `pip install transformers torch accelerate`

### How to run

1. Run all cells: load tokenizer and model, then generate quiz, (optionally use sample answers), score, and print.
2. For **interactive** mode: in your own copy, use `input("Your answer: ")` for each question instead of the sample-answers list, then call `score_answers` and `print_scores`.
