import re
def clean_text(text: str) -> str:
    """
    Clean raw message text by:
    - trimming leading/trailing spaces
    - normalizing multiple spaces
    - normalizing blank lines
    """
    if not text:
        return ""

    # Remove leading/trailing whitespace
    cleaned = text.strip()

    # Replace multiple spaces/tabs with a single space
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    # Replace 3+ newlines with max 2 newlines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned


def get_message_stats(text: str) -> dict:
    """
    Return basic message statistics for debugging / inspection.
    """
    if not text:
        return {
            "word_count": 0,
            "line_count": 0,
            "char_count": 0
        }

    lines = [line for line in text.splitlines() if line.strip()]
    words = text.split()

    return {
        "word_count": len(words),
        "line_count": len(lines),
        "char_count": len(text)
    }


def prepare_message_input(raw_message: str) -> dict:
    """
    Main helper function for preprocessing the incoming message.

    Returns a dictionary containing:
    - raw_message
    - cleaned_message
    - stats
    """
    cleaned_message = clean_text(raw_message)
    stats = get_message_stats(cleaned_message)

    return {
        "raw_message": raw_message,
        "cleaned_message": cleaned_message,
        "stats": stats
    }