"""
gemini_trading_code_generator.py

Usage:
    - Prepare you API Specification JSON file with your simulated API details.
    - Run: pip install google-genai.
    - Set GOOGLE_API_KEY env var before running.
    - Run: python gemini_trading_code_generator.py
    - The generated bot will be saved as `generated_trading_bot.py`.

Notes:
    - THIS GENERATES CODE FOR A SIMULATED ENVIRONMENT. Read and review generated code before running.
    - Keep your API keys safe.
"""

import os
import json
from typing import Dict, Any
from datetime import datetime

# Gemini client import (Google GenAI SDK)
try:
    from google import genai
    from google.genai import types
except Exception as e:
    raise RuntimeError("google-genai not installed. Run: pip install google-genai") from e


# ------------ Gemini / Prompting helpers -------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    # We won't fail here — the generator will raise when trying to call the client.
    pass

GEMINI_MODEL = "gemini-2.5-flash"
MAX_TOKEN_COUNT = 12000


def build_prompt(api_spec: Dict[str, Any], strategy: str = "sma_crossover") -> str:
    """
    Create a clear instruction for Gemini to generate the trading bot code.

    Strategy choices:
        - sma_crossover (default): simple moving-average crossover strategy
        - random: random buy/sell (for testing)
        - placeholder for the user to request others
    """
    now = datetime.utcnow().isoformat() + "Z"
    prompt = f"""
You are a code-writing assistant. Produce a single, self-contained Python script named `generated_trading_bot.py`
that implements a trading bot for a *simulated equities API*. The simulator has the following specification (JSON):
{json.dumps(api_spec, indent=2)}

Requirements for the generated script:
1. The script must be runnable as-is (except for inserting API keys/config). Use only stdlib + `requests` (no other external deps).
2. Implement a simple trading strategy: {strategy}. For `sma_crossover`, implement:
   - Fetch historical or recent prices (you may simulate historical by sampling current price in a loop if the API doesn't return history).
   - Compute short and long simple moving averages (e.g., 5-period and 20-period).
   - When short SMA crosses above long SMA: submit a MARKET or SIMULATED BUY order sized to use a configurable fraction of available cash.
   - When short SMA crosses below long SMA: submit a MARKET or SIMULATED SELL order to close position.
3. Use the API endpoints from the spec exactly (build URLs using base_url + path). Respect auth header scheme from spec.
4. Include robust error handling and logging (print statements acceptable).
5. Include a `--dry-run` flag that prints actions instead of placing orders.
6. Include a safe simulation mode: throttle requests, avoid rapid-fire orders, and include a configurable `min_time_between_trades_seconds`.
7. Add inline comments explaining important functions and a short README-like docstring at the top of the generated file describing how to configure and run it.
8. At the end of the generated file, add a __main__ section that demonstrates a short run (e.g., a 60-second loop) in dry-run mode.
9. Do NOT assume any third-party libraries beyond `requests`. Use dataclasses where helpful. Use typing annotations.
10. Always document any assumptions you make in a top-level comment block.
11. Keep the entire output as valid Python code only (no additional text around it).

Generate code now.
Timestamp for reproducibility: {now}
"""
    return prompt.strip()

# ------------ Gemini call -------------
def generate_code_with_gemini(prompt: str, model: str = GEMINI_MODEL, max_tokens: int = MAX_TOKEN_COUNT) -> str:
    """
    Call the Gemini model to generate the code.

    Uses google-genai SDK. Make sure env var GOOGLE_API_KEY or GOOGLE_API_KEY is set.
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError("No Google API key found. Set GOOGLE_API_KEY environment variable.")

    # Create client (per Google Gen AI quickstart)
    client = genai.Client(api_key=GOOGLE_API_KEY)

    # The SDK surface has varied; using the documented 'models.generate_content' style.
    # If your SDK differs, adapt accordingly.
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=max_tokens,
        )
    )

    text = None
    if hasattr(response, "text") and response.text:
        text = response.text
    else:
        # attempt to dig into typical structures
        try:
            # some SDKs return dict-like object
            if isinstance(response, dict):
                # Try common keys
                for k in ("text", "content", "output", "candidates"):
                    if k in response and response[k]:
                        text = json.dumps(response[k]) if not isinstance(response[k], str) else response[k]
                        break
            else:
                # object with attributes
                if hasattr(response, "output") and response.output:
                    # navigate first candidate -> text
                    out = response.output
                    if isinstance(out, (list, tuple)) and len(out) > 0:
                        first = out[0]
                        if isinstance(first, dict) and "content" in first:
                            text = first["content"][0].get("text")
                        elif hasattr(first, "content"):
                            text = first.content[0].text
        except Exception:
            pass

    if not text:
        raise RuntimeError("Could not extract generated text from Gemini response. Inspect `response` object: " + repr(response))
    
    return text

# ------------ Save & basic verification -------------
def basic_sanity_check(code_text: str) -> bool:
    """Do a quick check that the output looks like Python file and contains required sections."""
    checks = [
        "import requests" in code_text or "import urllib" in code_text,
        "def " in code_text,
        "if __name__" in code_text,
        "place_order" in code_text or "order" in code_text
    ]
    return all(checks)

def save_generated_file(code_text: str, filename: str = "generated_trading_bot.py") -> str:
    code_text = code_text.replace("```python","").replace("```","")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code_text)
    return os.path.abspath(filename)

# ------------ Main CLI -------------
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate trading bot code using Gemini (Google GenAI).")
    parser.add_argument("--api-spec", type=str, default="api_spec.json", help="Path to JSON file with API spec.")
    parser.add_argument("--out", type=str, default="generated_trading_bot.py", help="Output filename.")
    parser.add_argument("--model", type=str, default=GEMINI_MODEL, help="Gemini model to use.")
    parser.add_argument("--max-tokens", type=int, default=MAX_TOKEN_COUNT, help="Max tokens for generation.")
    parser.add_argument("--strategy", type=str, default="sma_crossover", help="Trading strategy to request.")
    args = parser.parse_args()

    with open(args.api_spec, "r", encoding="utf-8") as f:
        api_spec = json.load(f)

    prompt = build_prompt(api_spec, strategy=args.strategy)
    print("Calling Gemini to generate code... (this will use your GOOGLE_API_KEY)")
    generated = generate_code_with_gemini(prompt, model=args.model, max_tokens=args.max_tokens)

    print("Performing sanity checks on the generated code...")
    if not basic_sanity_check(generated):
        print("Warning: basic sanity checks failed. Still saving the file for inspection.")

    path = save_generated_file(generated, filename=args.out)
    print(f"Generated code saved to: {path}")
    print("Important: Review the generated code carefully before running against any system (even a simulator).")


if __name__ == "__main__":
    main()
