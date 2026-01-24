import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

MODEL = os.getenv("SECURECODE_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

SYSTEM_PROMPT = """You are a Python testing expert.
Generate pytest unit tests for the given code.
Include:
- Happy path tests
- Edge cases
- Error handling tests
Keep tests simple and clear."""

def generate_tests(code):
    """Generate unit tests for the given code."""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate tests for this code:\n\n{code}"}
            ],
            stream=True
        )

        result = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                result += chunk.choices[0].delta.content
                yield result

    except Exception as e:
        yield f"Error: {str(e)}"
