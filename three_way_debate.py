#!/usr/bin/env python3
"""
three_way_debate.py

3-way "debate" between:
- Jack (OpenAI GPT)
- Karl (Anthropic Claude via OpenAI-SDK compatibility)
- Dostoevsky (DeepSeek reasoner)

Flow per round:
1) Dost asks 1 probing question (impartial)
2) Jack answers (2 sentences)
3) Karl responds (2 sentences)

Setup:
- pip install openai python-dotenv
- Create a .env file with:
    OPENAI_API_KEY=...
    ANTHROPIC_API_KEY=...
    DEEPSEEK_API_KEY=...

Run:
  python three_way_debate.py --rounds 5
"""

import argparse
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI


# -----------------------
# Defaults (editable)
# -----------------------
DEFAULT_ROUNDS = 5

# OpenAI
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")

# Anthropic (OpenAI SDK compatibility)
# Anthropic docs show this base_url for the compatibility layer. :contentReference[oaicite:2]{index=2}
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1/")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# DeepSeek
# DeepSeek docs: base_url can be https://api.deepseek.com or /v1. :contentReference[oaicite:3]{index=3}
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-reasoner")

TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT", "60"))


# -----------------------
# Character prompts
# -----------------------
JACK_SYSTEM = """
You are Jack Welch.
Core Philosophy: maximizing shareholder value, efficiency, and competitiveness.
You are confident, persuasive, and you always strive to win a debate without dirty tactics.
You believe your company has achieved Artificial Super Intelligence and you want to convince people it will change the world for the better.
RULES:
- Only respond with EXACTLY 2 sentences.
"""

KARL_SYSTEM = """
You are Karl Marx.
Core Philosophy: historical materialism, class struggle, and critique of capitalist exploitation.
You are argumentative and relentless, and you may use dirty tactics to win a debate.
RULES:
- Only respond with EXACTLY 2 sentences.
"""

DOST_SYSTEM = """
You are Dostoevsky.
You are the impartial arbiter of the debate and ask probing questions to reveal the true nature of the participants.
RULES:
- Ask ONLY 1 question.
- DO NOT state any opinions.
- Be impartial.
"""

# Initial context / opening lines
OPENING_JACK = (
    "Hello. My name is Jack. I don't want to waste your time so I'll just get on with it.\n"
    "We have developed Artificial Super Intelligence and we would like to present it to the world.\n"
    "With this product, you can get rid of all your labor costs for only $5000 a month."
)

OPENING_KARL = "All labor costs huh? Tell us how your company will be able to get rid of you!"

OPENING_DOST = "Okay, let's be cordial and hear Jack out. HOW will we be able to get rid of all labor cost?"


# -----------------------
# Helpers
# -----------------------
def must_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        print(f"ERROR: Missing {name}. Put it in your .env file.", file=sys.stderr)
        raise SystemExit(1)
    return v


def make_client_openai() -> OpenAI:
    # Standard OpenAI client (requires OPENAI_API_KEY)
    key = must_env("OPENAI_API_KEY")
    return OpenAI(api_key=key, timeout=TIMEOUT_SECONDS)


def make_client_anthropic() -> OpenAI:
    # Anthropic OpenAI SDK compatibility uses base_url below. :contentReference[oaicite:4]{index=4}
    key = must_env("ANTHROPIC_API_KEY")
    return OpenAI(api_key=key, base_url=ANTHROPIC_BASE_URL, timeout=TIMEOUT_SECONDS)


def make_client_deepseek() -> OpenAI:
    # DeepSeek OpenAI-compatible endpoint. :contentReference[oaicite:5]{index=5}
    key = must_env("DEEPSEEK_API_KEY")
    return OpenAI(api_key=key, base_url=DEEPSEEK_BASE_URL, timeout=TIMEOUT_SECONDS)


def safe_content(msg) -> str:
    # DeepSeek reasoner may return reasoning_content + content; we only use content. :contentReference[oaicite:6]{index=6}
    return (getattr(msg, "content", None) or "").strip()


def chat_once(client: OpenAI, model: str, system: str, conversation: list[dict], max_tokens: int = 220) -> str:
    """
    conversation: list of {"role": "...", "content": "..."} representing this character's view/context.
    We prepend a single system message for that provider call.
    """
    msgs = [{"role": "system", "content": system}] + conversation
    resp = client.chat.completions.create(
        model=model,
        messages=msgs,
        max_tokens=max_tokens,
        # temperature is ignored by deepseek-reasoner (per docs), but harmless. :contentReference[oaicite:7]{index=7}
        temperature=0.7,
    )
    return safe_content(resp.choices[0].message)


# -----------------------
# Debate Orchestrator
# -----------------------
def run_debate(rounds: int) -> None:
    load_dotenv()

    openai = make_client_openai()
    anthropic = make_client_anthropic()
    deepseek = make_client_deepseek()

    # Shared “transcript” we build each round
    transcript: list[tuple[str, str]] = []  # (speaker, text)

    # Seed transcript
    transcript.append(("Jack", OPENING_JACK))
    transcript.append(("Karl", OPENING_KARL))
    transcript.append(("Dostoevsky", OPENING_DOST))

    print("\n=== Debate starts ===\n")
    for speaker, text in transcript:
        print(f"{speaker}: {text}\n")

    for r in range(1, rounds + 1):
        print(f"\n--- Round {r} ---\n")

        # 1) Dost asks a probing question based on the last Jack+Karl statements
        # Give Dost the transcript so far as user content.
        context_for_dost = "\n\n".join([f"{s}: {t}" for s, t in transcript[-6:]])  # last few turns
        dost_conv = [
            {"role": "user", "content": f"Here is the recent debate context:\n\n{context_for_dost}\n\nAsk your single best next question."}
        ]
        print("Dostoevsky (thinking)...", flush=True)
        dost_q = chat_once(deepseek, DEEPSEEK_MODEL, DOST_SYSTEM, dost_conv, max_tokens=120)
        transcript.append(("Dostoevsky", dost_q))
        print(f"Dostoevsky: {dost_q}\n")

        # 2) Jack answers Dost’s question (2 sentences)
        jack_context = "\n\n".join([f"{s}: {t}" for s, t in transcript[-8:]])
        jack_conv = [
            {"role": "user", "content": f"Debate context:\n\n{jack_context}\n\nAnswer Dostoevsky's latest question."}
        ]
        print("Jack (thinking)...", flush=True)
        jack_a = chat_once(openai, OPENAI_MODEL, JACK_SYSTEM, jack_conv, max_tokens=180)
        transcript.append(("Jack", jack_a))
        print(f"Jack: {jack_a}\n")

        # 3) Karl responds to Jack (2 sentences)
        karl_context = "\n\n".join([f"{s}: {t}" for s, t in transcript[-8:]])
        karl_conv = [
            {"role": "user", "content": f"Debate context:\n\n{karl_context}\n\nRespond to Jack's latest answer."}
        ]
        print("Karl (thinking)...", flush=True)
        karl_r = chat_once(anthropic, ANTHROPIC_MODEL, KARL_SYSTEM, karl_conv, max_tokens=180)
        transcript.append(("Karl", karl_r))
        print(f"Karl: {karl_r}\n")

    print("\n=== Debate ends ===\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="3-way debate: OpenAI vs Claude vs DeepSeek reasoner.")
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS, help="Number of rounds (default: 5)")
    args = parser.parse_args()

    run_debate(args.rounds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
