import os, re
from openai import OpenAI
from dotenv import load_dotenv

from prompts.prompts import TEACHER_SYSTEM

load_dotenv()

OPENROUTER_URL     = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

TEACHER_MODEL         = "meta-llama/llama-3.1-8b-instruct"
STUDENT_BASE_MODEL    = "Qwen/Qwen2.5-0.5B"

QUESTION              = "What does this cost to the nearest dollar?"
PREFIX                = "Price is $"
COT_RESPONSE_TEMPLATE = "Reasoning: "


def teacher_user(summary: str) -> str:
    return (
        f"Product:\n{summary}\n\n"
        "Reason about the price in 2-3 sentences "
        "(consider category, brand signals, quality tier), "
        "then output on a new line:\n"
        f"{PREFIX}<number>.00"
    )


def _extract(text: str) -> tuple[str, float | None]:
    """Parse teacher response into (reasoning, price).

    Tries progressively looser patterns so minor formatting variations don't fail.
    """
    patterns = [
        r"Price is \$\s*(\d+(?:\.\d+)?)",   # "Price is $49.00"
        r"price[:\s]+\$\s*(\d+(?:\.\d+)?)", # "Price: $49"
        r"\$\s*(\d+(?:\.\d+)?)",             # bare "$49"
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            price     = float(m.group(1))
            reasoning = text[: m.start()].strip()
            return reasoning, price
    return "", None


def make_cot_prompt(summary: str) -> str:
    return f"{QUESTION}\n\n{summary}\n\n"


def make_cot_completion(reasoning: str, price: float) -> str:
    return f"{COT_RESPONSE_TEMPLATE}{reasoning}\n\n{PREFIX}{round(price)}.00"


def make_standard_prompt(summary: str) -> str:
    return f"{QUESTION}\n\n{summary}\n\n{PREFIX}"


def annotate(item, client: OpenAI) -> tuple[str, float | None]:
    """Call teacher model and return (reasoning, predicted_price)."""
    try:
        resp = client.chat.completions.create(
            model=TEACHER_MODEL,
            messages=[
                {"role": "system", "content": TEACHER_SYSTEM},
                {"role": "user",   "content": teacher_user(item.summary)},
            ],
            temperature=0.3,
            max_tokens=200,
        )
        return _extract(resp.choices[0].message.content.strip())
    except Exception as e:
        print(f"[annotate error] {type(e).__name__}: {e}")
        return "", None


def zero_shot_predict(summary: str, client: OpenAI) -> str:
    """Zero-shot price prediction via OpenRouter."""
    try:
        resp = client.chat.completions.create(
            model=TEACHER_MODEL,
            messages=[
                {"role": "user", "content": f"{QUESTION}\n\n{summary}\n\n{PREFIX}"}
            ],
            temperature=0.1,
            max_tokens=10,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return "0"
