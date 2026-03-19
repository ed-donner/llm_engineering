"""
Gradio chat app for Beat the Numbers RAG.

Run from week5:
  cd week5 && uv run python community-contributions/adams-bolaji/app.py

Or from repo root:
  PYTHONPATH=week5 uv run python week5/community-contributions/adams-bolaji/app.py
"""
import sys
from pathlib import Path

WEEK5 = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WEEK5))

import gradio as gr
from answer import answer_question


def chat(message, history):
    """Gradio chat handler: answer with RAG and return text only."""
    answer, _ = answer_question(message, history)
    return answer


def main():
    gr.ChatInterface(chat, type="messages", title="Insurellm RAG (Beat the Numbers)").launch(
        inbrowser=True
    )


if __name__ == "__main__":
    main()
