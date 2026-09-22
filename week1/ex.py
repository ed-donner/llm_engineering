from openai import OpenAI
import os
from IPython import get_ipython
from IPython.display import Markdown, display, update_display

question = """
Please explain what this code does and why:
yield from {book.get("author") for book in books if book.get("author")}
"""

base_url = os.getenv("DEEPSEEK_URL", "http://localhost:12434/v1/")
model = os.getenv("DEEPSEEK_MODEL", "ai/deepseek-r1-distill-llama:latest")


client = OpenAI(base_url=base_url, api_key="not-needed")

messages = [
    {
        "role": "system",
        "content": "you a helpful assistant that explains code snippets, and provides examples, and explains why the code is written that way.",
    },
    {"role": "user", "content": question},
]


stream = client.chat.completions.create(
    model=model,
    messages=messages,
    stream=True,
)

response = ""
display_handle = None

for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        response += content
        if display_handle is not None:
            update_display(Markdown(response), display_id=display_handle.display_id)
        else:
            print(content, end="", flush=True)

