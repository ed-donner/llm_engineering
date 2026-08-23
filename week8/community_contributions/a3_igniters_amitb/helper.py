import re
import json


def extract_price(text: str) -> float:
    """Extract the first numeric value from a string."""
    text = text.replace("$", "").replace(",", "").strip()
    match = re.search(r"[-+]?\d*\.?\d+", text)
    return float(match.group()) if match else 0.0


def parse_json_safe(text: str) -> dict:
    """Parse JSON from an LLM response, stripping markdown fences if present."""
    text = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {}
