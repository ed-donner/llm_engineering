from openai import OpenAI
import os
from prompts.docstring_prompt import SYSTEM_PROMPT, build_prompt
from utils.parsers import extract_code

def run(python_code: str, model:str, client: OpenAI) -> str:
    """
    Generate docstrings for python code use LLM.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(python_code)}
        ],
        temperature=0.2
    )
    raw = response.choices[0].message.content
    return extract_code(raw, lang="python")
