#!/usr/binpython3

import os
from dotenv import load_dotenv
from openai import OpenAI
import anthropic

gpt_messages = ["Hi there! is this the right room for an argument?"]
claude_messages = ["No it is not"]

def load_api_keys():
    # Load environment variables in a file called .env
    load_dotenv(override=True)
    openai_api_key = os.getenv('OPENAI_API_KEY')
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

    # Check the key
    if not openai_api_key:
        return "Error: No OpenAI API key was found!"
    elif not anthropic_api_key:
        return "Error: No Anthropic API key was found!"
    else:
        return "API keys found!"

def call_gpt(openai):
    gpt_model = "gpt-4.1-mini"
    gpt_system = "You are a patient visiting the Argument Clinic from the famous Monty Python sketch. \
            You are very eager to have a real arguement and will quickly be irritated if someone merely contradicts you."
    messages = [{"role": "system", "content": gpt_system}]
    for gpt, claude in zip(gpt_messages, claude_messages):
        messages.append({"role": "assistant", "content": gpt})
        messages.append({"role": "user", "content": claude})
    completion = openai.chat.completions.create(
        model=gpt_model,
        messages=messages
    )
    return completion.choices[0].message.content

def call_claude(claude):
    claude_model = "claude-3-5-haiku-latest"
    claude_system = "You are a proffesional arguer at the Argument Clinic from the famous Monty Python sketch. \
            You love to contradict whatever the person talking to you is saying."
    messages = []
    for gpt, claude_message in zip(gpt_messages, claude_messages):
        messages.append({"role": "user", "content": gpt})
        messages.append({"role": "assistant", "content": claude_message})
    messages.append({"role": "user", "content": gpt_messages[-1]})
    message = claude.messages.create(
        model=claude_model,
        system=claude_system,
        messages=messages,
        max_tokens=500
    )
    return message.content[0].text

def main():
    load_api_keys()
    openai = OpenAI()
    claude = anthropic.Anthropic()

    print(f"GPT:\n{gpt_messages[0]}\n")
    print(f"Claude:\n{claude_messages[0]}\n")

    for i in range(5):
        gpt_next = call_gpt(openai)
        print(f"GPT:\n{gpt_next}\n")
        gpt_messages.append(gpt_next)
        claude_next = call_claude(claude)
        print(f"Claude:\n{claude_next}\n")
        claude_messages.append(claude_next)

if __name__ == "__main__":
    main()
