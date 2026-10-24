from openai import OpenAI
from prompts.testgen_prompt import SYSTEM_PROMPT, build_prompt
from utils.parsers import extract_code

def run(documented_code: str, model: str, client: OpenAI) -> str:
    """
    Generate pytest unit tests from documented code.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(documented_code)}
        ],
        temperature=0.3
    )
    raw = response.choices[0].message.content
    return extract_code(raw, lang="python")