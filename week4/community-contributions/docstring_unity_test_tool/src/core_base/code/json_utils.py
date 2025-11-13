import json
import re


def safe_json_loads(text: str):
    """
    Attempt to parse a JSON string while correcting common formatting mistakes.
    
    This function removes trailing commas and certain unwanted characters before attempting to load the JSON.
    
    Args:
      text (str): The JSON string to be parsed.
    Returns:
      dict or None: The parsed JSON object if successful, or None if parsing fails.
    """
    cleaned = re.sub(r",(\s*[}\]])", r"\1", text.strip())  # remove trailing commas
    cleaned = cleaned.replace("\r", "").replace("\x00", "")
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("Error al parsear JSON incluso tras limpieza:", e)
        print("Contenido limpio:")
        print(cleaned)
        return None