import re

def clean_text(text):
    # Remove weird symbols
    text = re.sub(r'[^a-zA-Z0-9\n\s.,:()\-\[\]]', '', text)

    # Normalize newlines
    text = re.sub(r'\n+', '\n', text)

    lines = text.split("\n")
    filtered_lines = []

    for line in lines:
        line = line.strip()

        # Skip short garbage
        if len(line) < 5:
            continue

        # Remove UI noise
        if any(word in line.lower() for word in [
            "blog", "editorial", "home", "course", "solve"
        ]):
            continue

        # Keep only relevant content
        # if not any(keyword in line.lower() for keyword in [
        #     "input", "output", "example", "given", "return", "pointer"
        # ]):
        #     continue

        # ✅ FIXED: append line, not lines
        filtered_lines.append(line)

    cleaned = "\n".join(filtered_lines)

    return cleaned.strip()