from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_client():
    global _client

    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        _client = OpenAI(api_key=api_key)

    return _client


def get_embedding(text):
    if not text.strip():
        return None

    client = get_client()

    res = client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )

    return res.data[0].embedding