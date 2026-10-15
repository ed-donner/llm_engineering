#!/usr/bin/env python3
"""
technical_qa_rater.py (Ollama-only)

What it does:
- Takes a technical question (CLI)
- Gets answers from TWO local Ollama models (OpenAI-compatible endpoint)
- Each model scores the other model's answer (JSON score + reason)
- Prints answers, scores, and a simple winner result

Requirements:
  pip install openai

Ollama:
  - Install Ollama (Windows): https://ollama.com/download
  - Ensure server is running (usually auto): http://localhost:11434
  - Pull models:
      ollama pull gemma3:1b
      ollama pull llama3.2:1b

Run:
  python technical_qa_rater.py -q "What is idempotency and how is it used in API design?"
"""

import argparse
import json
import sys
from typing import Any, Dict, List

from openai import OpenAI


DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL_A = "gemma3:1b"
DEFAULT_MODEL_B = "llama3.2:1b"

SYSTEM_PROMPT = (
    "You are a technical assistant. Answer technical questions clearly, accurately, "
    "and with helpful examples when relevant. Keep it well-structured."
)

SCORING_SYSTEM_PROMPT = """You are a strict scoring system.
You will be shown a technical question and an answer.

Return ONLY valid JSON with:
- "score": integer 0..100
- "reason": short explanation (max 60 words)
No extra text outside the JSON.
"""


def build_messages(question: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]


def print_block(title: str, text: str) -> None:
    print("\n" + title)
    print("=" * len(title))
    print(text)


def get_answer(client: OpenAI, model: str, messages: List[Dict[str, str]]) -> str:
    # Limit tokens so it responds quickly and doesn't hang for too long
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.4,
        max_tokens=350,
    )
    return (resp.choices[0].message.content or "").strip()


def score_answer(
    client: OpenAI,
    model: str,
    question: str,
    answer: str,
) -> Dict[str, Any]:
    user_prompt = f"Question:\n{question}\n\nAnswer to score:\n{answer}\n"

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SCORING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=120,
    )

    raw = (resp.choices[0].message.content or "").strip()

    # Expect JSON-only; if the model violates format, keep raw output for debugging
    try:
        data = json.loads(raw)
        # Basic validation
        score = data.get("score")
        reason = data.get("reason")
        if not isinstance(score, int):
            return {"score": None, "reason": None, "raw": raw}
        if not isinstance(reason, str):
            return {"score": score, "reason": "", "raw": raw}
        return {"score": score, "reason": reason}
    except json.JSONDecodeError:
        return {"score": None, "reason": None, "raw": raw}


def main() -> int:
    parser = argparse.ArgumentParser(description="Local-only Q&A + cross-scoring using Ollama.")
    parser.add_argument("-q", "--question", required=True, help="Your technical question (use quotes).")
    parser.add_argument("--model-a", default=DEFAULT_MODEL_A, help=f"Model A (default: {DEFAULT_MODEL_A})")
    parser.add_argument("--model-b", default=DEFAULT_MODEL_B, help=f"Model B (default: {DEFAULT_MODEL_B})")
    parser.add_argument("--base-url", default=DEFAULT_OLLAMA_BASE_URL, help="Ollama OpenAI-compatible base URL")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds (default: 60)")
    args = parser.parse_args()

    # Ollama OpenAI-compatible endpoint; api_key can be any non-empty string.
    # timeout prevents hanging forever.
    client = OpenAI(base_url=args.base_url, api_key="ollama", timeout=args.timeout)

    question = args.question.strip()
    messages = build_messages(question)

    # 1) Two answers (A and B) with progress prints (flush=True so you see it instantly)
    try:
        print(f"Querying {args.model_a}...", flush=True)
        answer_a = get_answer(client, args.model_a, messages)
    except Exception as e:
        print(f"ERROR: Model A request failed: {e}", file=sys.stderr)
        print("Tip: confirm Ollama is running: curl -s http://localhost:11434/api/tags", file=sys.stderr)
        return 1

    try:
        print(f"Querying {args.model_b}...", flush=True)
        answer_b = get_answer(client, args.model_b, messages)
    except Exception as e:
        print(f"ERROR: Model B request failed: {e}", file=sys.stderr)
        print("Tip: pull the model first: ollama pull <model>", file=sys.stderr)
        return 1

    print_block(f"Answer from {args.model_a}", answer_a)
    print_block(f"Answer from {args.model_b}", answer_b)

    # 2) Cross-score
    print(f"Scoring: {args.model_a} -> {args.model_b}...", flush=True)
    score_a_on_b = score_answer(client, args.model_a, question, answer_b)

    print(f"Scoring: {args.model_b} -> {args.model_a}...", flush=True)
    score_b_on_a = score_answer(client, args.model_b, question, answer_a)

    print_block(f"{args.model_a} scores {args.model_b}", json.dumps(score_a_on_b, indent=2))
    print_block(f"{args.model_b} scores {args.model_a}", json.dumps(score_b_on_a, indent=2))

    # 3) Simple winner logic (only if both scores parsed as ints)
    s1 = score_a_on_b.get("score")
    s2 = score_b_on_a.get("score")

    if isinstance(s1, int) and isinstance(s2, int):
        if s1 > s2:
            winner = f"{args.model_b}'s answer wins (judged by {args.model_a})"
        elif s2 > s1:
            winner = f"{args.model_a}'s answer wins (judged by {args.model_b})"
        else:
            winner = "Tie"
        print_block(
            "Result",
            f"{args.model_a} -> ({args.model_b} answer): {s1}\n"
            f"{args.model_b} -> ({args.model_a} answer): {s2}\n"
            f"Winner: {winner}",
        )
    else:
        print_block(
            "Result",
            "Could not parse one/both scores as JSON.\n"
            "Check the 'raw' field in the scorer outputs above (if present).",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
