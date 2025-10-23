#!/usr/bin/env python3
"""
Technical Assistant - Week 1 Exercise
Supports both OpenAI API and Ollama
"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI


class TechnicalAssistant:
    """Technical Q&A assistant - works with OpenAI, OpenRouter, or Ollama"""

    def __init__(self, model="llama3.2", provider="ollama"):
        api_key = os.getenv('OPENAI_API_KEY')

        if provider == "openai":
            # Use OpenAI API
            self.client = OpenAI(api_key=api_key)
            self.model = model
            print(f"Using OpenAI with model: {self.model}")
        elif provider == "openrouter":
            # Use OpenRouter
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key
            )
            self.model = model
            print(f"Using OpenRouter with model: {self.model}")
        else:
            # Use Ollama (local)
            self.client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama"
            )
            self.model = model
            print(f"Using Ollama with model: {self.model}")

        # System prompt - tells the model how to behave
        self.system_prompt = """You are a helpful technical assistant who explains programming concepts clearly.
When answering:
- Give clear explanations
- Include code examples when relevant
- Explain both what and why
- Keep it practical and easy to understand"""

    def ask(self, question, stream=True):
        """Ask a technical question and get an answer"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": question}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream
            )

            if stream:
                answer = ""
                print()
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        text = chunk.choices[0].delta.content
                        print(text, end="", flush=True)
                        answer += text
                print("\n")
                return answer
            else:
                result = response.choices[0].message.content
                print(f"\n{result}\n")
                return result

        except Exception as e:
            print(f"Error: {e}")
            return None

    def chat(self):
        """Start interactive chat mode"""
        print("\n" + "="*60)
        print("Technical Assistant - Ask me anything!")
        print("="*60)
        print(f"Model: {self.model}")
        print("Type 'quit' or 'exit' to stop")
        print("="*60 + "\n")

        while True:
            try:
                question = input(">> ")

                if question.strip().lower() in ['quit', 'exit', 'q']:
                    print("\nBye!")
                    break

                if not question.strip():
                    continue

                self.ask(question)

            except KeyboardInterrupt:
                print("\n\nBye!")
                break
            except Exception as e:
                print(f"Error: {e}")


def main():
    load_dotenv()

    # Determine which provider to use
    provider = "ollama"  # default
    if "--openai" in sys.argv:
        provider = "openai"
    elif "--openrouter" in sys.argv:
        provider = "openrouter"

    # Default models based on provider
    if provider == "openai":
        model = "gpt-4o-mini"
    elif provider == "openrouter":
        model = "meta-llama/llama-3.2-3b-instruct:free"
    else:
        model = "llama3.2"

    # Check if user specified a custom model
    if "--model" in sys.argv:
        try:
            idx = sys.argv.index("--model")
            model = sys.argv[idx + 1]
        except:
            pass

    assistant = TechnicalAssistant(model=model, provider=provider)

    # Single question mode
    if "--question" in sys.argv:
        try:
            idx = sys.argv.index("--question")
            question = sys.argv[idx + 1]
            print(f"\nQuestion: {question}\n")
            assistant.ask(question)
            return
        except:
            print("Invalid question format")
            return

    # Interactive mode
    assistant.chat()


if __name__ == "__main__":
    main()
