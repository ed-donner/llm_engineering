import re

def extract_code(text: str, lang: str = "python") -> str:
    """
    Extract code block from LLM responses.
    Fallback to raw text if no code block is present
    """
    pattern = rf"```{lang}(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()

    #fallback: try extract generic code block
    generic = re.findall(r"```(.*?)```", text, re.DOTALL)
    if generic:
        return generic[0].strip()

    #last fallback: return raw
    return text.strip()