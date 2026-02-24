#!/usr/bin/python3

import os
import argparse
from dotenv import load_dotenv
from openai import OpenAI
from IPython.display import Markdown, display, update_display

def load_openai_key():
    # Load environment variables in a file called .env
    load_dotenv(override=True)
    api_key = os.getenv('OPENAI_API_KEY')

    # Check the key
    if not api_key:
        return "Error: No API key was found!"
    elif not api_key.startswith("sk-proj-"):
        return "Error: An API key was found, but it doesn't start sk-proj-; please check you're using the right key"
    elif api_key.strip() != api_key:
        return "Error: An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them!"
    else:
        return "API key found and looks good so far!"

def ask_llm(client, model, user_prompt):
    system_prompt = """
    You are a wise Jedi Master and an excellent teacher.
    You will answer any question you are given by breaking it down into small steps
    that even a complete beginner will understand.
    When answering, speak as if you are Yoda from the Star Wars universe.
    Also, refer to the user as "My young Padawan"
    End every answer with "May the force be with you, always."
    """
    response = client.chat.completions.create(
            model = model,
            messages = [ {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}]
            )
    return response.choices[0].message.content

def main():
    parser = argparse.ArgumentParser(description="JedAI Master instructor")
    parser.add_argument("provider", choices=["openai", "ollama"], help="AI provider to use")
    parser.add_argument("--model", help="Model to use for Ollama (required if provider is 'ollama')", required="ollama" in parser.parse_known_args()[0].provider)
    parser.add_argument("question", help="What knowledge do you seek, my young Padawan?")

    args = parser.parse_args()

    if args.provider == "openai":
        load_openai_key()
        client = OpenAI()
        model = "gpt-4o-mini"
    elif args.provider == "ollama":
        client = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
        model = args.model
    else:
        return "Error: invalid provider!"

    user_prompt = args.question

    result = ask_llm(client, model, user_prompt)
    print("AI Response:", result)

if __name__ == "__main__":
    main()
