from openai import OpenAI
from prompts.selfheal_prompt import SYSTEM_PROMPT, build_prompt
from utils.parsers import extract_code

def run(
    source_code: str,
    test_code: str,
    errors: str,
    attempt: int,
    model: str,
    client: OpenAI
) -> str:
    """
    Fix source code berdasarkan pytest error output.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(source_code, test_code, errors, attempt)}
        ],
        temperature=0.1  # rendah — butuh deterministik untuk fixing
    )
    raw = response.choices[0].message.content
    return extract_code(raw, lang="python")