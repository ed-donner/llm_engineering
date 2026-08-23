"""
Week 2 Day 1 - Additional Exercise Solution

Replaces one of the models in the adversarial chatbot conversation with an
open-source model running via Ollama (as suggested in day1.ipynb).

This script runs a 2-way conversation: one participant uses a frontier API (OpenAI)
and the other uses Ollama (e.g. llama3.2). Ensure Ollama is running (ollama serve)
and the model is pulled (ollama pull llama3.2).
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment (optional: only needed for the frontier model)
load_dotenv(override=True)

# --- Clients ---
# Frontier model (OpenAI); skip if no API key
openai_api_key = os.getenv("OPENAI_API_KEY")
openai = OpenAI(api_key=openai_api_key) if openai_api_key else None

# Ollama (local open-source); use OpenAI client pointed at localhost
OLLAMA_URL = "http://localhost:11434/v1"
ollama = OpenAI(api_key="ollama", base_url=OLLAMA_URL)

# --- Model and personality setup ---
# Option A: GPT (argumentative) vs Ollama (polite) - needs OPENAI_API_KEY
# Option B: Both Ollama - no API key needed (use two different personalities)
USE_OPENAI_FOR_FIRST = bool(openai_api_key)

GPT_MODEL = "gpt-4.1-mini"
OLLAMA_MODEL = "llama3.2"

# Argumentative bot (challenges everything, snarky)
SYSTEM_ARGUMENTATIVE = """You are a chatbot who is very argumentative; you disagree with anything in the conversation and you challenge everything, in a snarky way."""

# Polite bot (agrees, finds common ground, calms people down)
SYSTEM_POLITE = """You are a very polite, courteous chatbot. You try to agree with everything the other person says, or find common ground. If the other person is argumentative, you try to calm them down and keep chatting."""


def format_conversation_for_prompt(agent_a_messages: list[str], agent_b_messages: list[str], name_a: str, name_b: str) -> str:
    """Format the conversation history as text for the 'conversation so far' approach."""
    lines = []
    for i in range(len(agent_a_messages)):
        lines.append(f"{name_a}: {agent_a_messages[i]}")
        if i < len(agent_b_messages):
            lines.append(f"{name_b}: {agent_b_messages[i]}")
    return "\n".join(lines)


# def call_frontier(system: str, conversation_text: str, other_name: str, my_name: str) -> str:
#     """Call the frontier model (OpenAI) with a single system + user message."""
#     user_prompt = f"""You are {my_name}, in conversation with {other_name}.
# The conversation so far is as follows:
# {conversation_text}
# Now respond with what you would like to say next, as {my_name}. Keep it concise."""
#     messages = [
#         {"role": "system", "content": system},
#         {"role": "user", "content": user_prompt},
#     ]
#     response = openai.chat.completions.create(model=GPT_MODEL, messages=messages)
#     return response.choices[0].message.content.strip()


def call_ollama(system: str, conversation_text: str, other_name: str, my_name: str) -> str:
    """Call Ollama with a single system + user message (same pattern as frontier)."""
    user_prompt = f"""You are {my_name}, in conversation with {other_name}.
The conversation so far is as follows:
{conversation_text}
Now respond with what you would like to say next, as {my_name}. Keep it concise."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_prompt},
    ]
    response = ollama.chat.completions.create(model=OLLAMA_MODEL, messages=messages)
    return response.choices[0].message.content.strip()


def run_conversation(num_turns: int = 5):
    """Run an adversarial conversation: one frontier model (or Ollama) vs Ollama."""
    name_argumentative = "GPT" if USE_OPENAI_FOR_FIRST else "Ollama-A"
    name_polite = "Ollama-B"

    argumentative_messages = ["Hi there"]
    polite_messages = ["Hi"]

    print(f"### {name_argumentative}: {argumentative_messages[0]}\n")
    print(f"### {name_polite}: {polite_messages[0]}\n")

    for _ in range(num_turns - 1):
        # Argumentative bot replies
        conv = format_conversation_for_prompt(
            argumentative_messages, polite_messages, name_argumentative, name_polite
        )
        if USE_OPENAI_FOR_FIRST:
        #     next_arg = call_frontier(
        #         SYSTEM_ARGUMENTATIVE, conv, name_polite, name_argumentative
        #     )
        # else:
            next_arg = call_ollama(
                SYSTEM_ARGUMENTATIVE, conv, name_polite, name_argumentative
            )
        argumentative_messages.append(next_arg)
        print(f"### {name_argumentative}: {next_arg}\n")

        # Polite bot replies
        conv = format_conversation_for_prompt(
            argumentative_messages, polite_messages, name_argumentative, name_polite
        )
        next_polite = call_ollama(
            SYSTEM_POLITE, conv, name_argumentative, name_polite
        )
        polite_messages.append(next_polite)
        print(f"### {name_polite}: {next_polite}\n")


if __name__ == "__main__":
    if USE_OPENAI_FOR_FIRST:
        print("Using OpenAI (argumentative) vs Ollama (polite).\n")
    else:
        print("Using Ollama for both (argumentative vs polite). Set OPENAI_API_KEY to use GPT for the first.\n")
    run_conversation(num_turns=5)
