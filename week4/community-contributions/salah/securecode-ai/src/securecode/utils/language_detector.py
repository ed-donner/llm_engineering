"""Simple language detection for code."""


def detect_language(code: str) -> str:
    """
    Detect programming language from code snippet.

    Args:
        code: Source code string

    Returns:
        Detected language name
    """
    code_lower = code.lower()

    # Python detection
    if any(keyword in code for keyword in ["def ", "import ", "from ", "class "]):
        if "print(" in code or "__init__" in code:
            return "Python"

    # JavaScript detection
    if any(keyword in code for keyword in ["function ", "const ", "let ", "var "]):
        if "console.log" in code or "=>" in code:
            return "JavaScript"

    # Java detection
    if "public class" in code or "public static void main" in code:
        return "Java"

    # C++ detection
    if "#include" in code or "std::" in code or "cout" in code:
        return "C++"

    # Go detection
    if "package main" in code or "func " in code and "import (" in code:
        return "Go"

    # Rust detection
    if "fn " in code and ("let " in code or "mut " in code):
        return "Rust"

    # Default to Python if unsure
    return "Python"
