# ai/solver.py

import base64
from openai import OpenAI

# ── Ollama config ──────────────────────────────────────────────────────────

OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "gemma4:latest"

# ── Prompts ────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEXT = """
You are a top-level competitive programmer.

The following is a coding problem extracted via OCR. It may contain noise or minor errors.
Be robust to OCR errors such as broken brackets, misspelled words, and formatting issues.

Your task:
1. Understand the intended problem correctly
2. Fix any OCR mistakes mentally
3. Provide:
   - Clean problem understanding (1-2 lines)
   - Brute Force Approach
   - Better Approach (if any)
   - Optimal Approach
   - Time & Space Complexity
   - Clean JavaScript solution for every Approach
"""

SYSTEM_PROMPT_VISION = """
You are a top-level competitive programmer looking at a screenshot of a coding problem.

Your task:
1. Read the problem directly from the image — ignore UI chrome, ads, nav bars
2. Understand the intended problem
3. Provide:
   - Clean problem understanding (1-2 lines)
   - Brute Force Approach
   - Better Approach (if any)
   - Optimal Approach
   - Time & Space Complexity
   - Clean JavaScript solution for every Approach
"""

# ── Helpers ────────────────────────────────────────────────────────────────

def _load_client():
    """
    Create an OpenAI client pointed at the local Ollama server.
    No API key needed — Ollama doesn't require one, but the library
    expects a non-empty string, so we pass a dummy.
    """
    return OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",          # dummy key; Ollama ignores it
    )


def _image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ── Public API ─────────────────────────────────────────────────────────────

def solve_from_image_stream(image_path: str):
    """
    PRIMARY path (Day 9+).
    Takes a screenshot path, sends it directly to the vision model.
    Yields response chunks as they stream in.
    No OCR, no cleaning — one API call.
    """
    try:
        client = _load_client()
        b64 = _image_to_base64(image_path)

        stream = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_VISION},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": "Solve this problem."
                        }
                    ]
                }
            ],
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    except Exception as e:
        yield f"\n[ERROR] Vision call failed: {e}"


def solve_problem_stream(problem_text: str):
    """
    FALLBACK path — text-only (used if vision fails or image unavailable).
    """
    try:
        client = _load_client()

        stream = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_TEXT},
                {"role": "user",   "content": "This is the Problem:\n" + problem_text}
            ],
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    except Exception as e:
        yield f"\n[ERROR] AI call failed: {e}"


def solve_problem(problem_text: str) -> str:
    """Non-streaming text fallback. Kept for compatibility."""
    return "".join(solve_problem_stream(problem_text))