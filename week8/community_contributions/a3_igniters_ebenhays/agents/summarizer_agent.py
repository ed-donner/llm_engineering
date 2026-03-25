import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")


class SummarizerAgent:

    def __init__(self, model="gpt-4o-mini"):
        self.model = model
        self.client = OpenAI()

    def summarize(self, text: str) -> str:
        if not text:
            return ""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes news articles.",
                    },
                    {
                        "role": "user",
                        "content": f"Summarize the following news article in 3 concise sentences. Be concise and to the point.\n\n{text}\n",
                    },
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error summarizing text: {e}")
            return None
