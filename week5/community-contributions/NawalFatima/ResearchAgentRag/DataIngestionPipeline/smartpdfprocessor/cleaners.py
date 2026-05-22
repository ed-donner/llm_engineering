"""
cleaners.py — Text cleaning and content detection for RAG chunks.

Handles:
- Cleaning extraction artifacts (temp paths, image refs, page markers)
- Detecting broken/corrupted tables
- Equation detection flag for chunk metadata
"""

import re


def remove_ocr_noise(text: str) -> str:
    replacements = {
        "�": "",
        "~~_√_~~": "sqrt",
        "_[√]": "sqrt",
        "_·_": "·",
        "_._": ".",
        "_[−]_": "-",
        "_[×]_": "×",
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    # Fix broken subscript-style OCR artifacts
    text = re.sub(r"_\[(.*?)\]_", r"\1", text)
    text = re.sub(r"_\[([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[([a-zA-Z0-9]+)\]_", r"\1", text)

    # Remove isolated page numbers
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

    # Collapse excessive spacing
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

# ------------------------------------------------------------------ #
# TEXT CLEANING
# ------------------------------------------------------------------ #

def clean_chunk_text(content: str) -> str:
    """
    Cleans temporary artifacts from extracted text before embedding.
    """
    # temp file image refs (Windows + Linux)
    content = re.sub(
        r"!\[\]\([^)]+(?:AppData/Local/Temp|/tmp|Temp)[^)]+\)",
        "",
        content,
        flags=re.IGNORECASE,
    )

    # remaining markdown image refs
    content = re.sub(r"!\[\]\([^)]+\)", "", content)

    # page markers injected during extraction
    content = re.sub(r"\[Page \d+\]\n*", "", content)

    # collapse excessive newlines
    content = re.sub(r"\n{3,}", "\n\n", content)

    content = remove_ocr_noise(content)

    return content.strip()


