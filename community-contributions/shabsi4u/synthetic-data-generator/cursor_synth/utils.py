import json
import re
from typing import Any, Optional

def safe_json_load(text: str) -> Optional[Any]:
    """
    Attempt to parse JSON. Heuristics:
      1) direct json.loads
      2) extract first [...] block
      3) extract first {...} block
      4) try to find JSON after common prefixes
    Returns parsed object or None.
    """
    # Clean up the text first
    text = text.strip()
    
    # Debug: Print what we're trying to parse
    print(f"DEBUG: Attempting to parse JSON from text (length: {len(text)})")
    print(f"DEBUG: First 200 chars: {text[:200]}")
    
    # First, try to remove <think> tags and extract content after them
    if '<think>' in text:
        print(f"DEBUG: Found <think> tag in text")
        # Look for </think> tag
        think_end = text.find('</think>')
        if think_end != -1:
            text_after_think = text[think_end + 8:].strip()
            print(f"DEBUG: Found </think> tag, trying content after: {text_after_think[:200]}")
            text = text_after_think
        else:
            # No closing tag found, try to extract everything after <think>
            think_start = text.find('<think>')
            if think_start != -1:
                # Try to find where thinking ends (look for JSON-like content)
                potential_json_start = text.find('[', think_start)
                if potential_json_start != -1:
                    text = text[potential_json_start:].strip()
                    print(f"DEBUG: No </think> tag found, trying content after <think>: {text[:200]}")
                else:
                    print(f"DEBUG: No </think> tag and no JSON found after <think>")
    
    try:
        result = json.loads(text)
        print(f"DEBUG: Direct JSON parse successful")
        return result
    except Exception as e:
        print(f"DEBUG: Direct JSON parse failed: {e}")

    # Try to find JSON array first (most common for our use case)
    # Use a more aggressive regex to find arrays, including nested ones
    arr_match = re.search(r'(\[[\s\S]*?\])', text, flags=re.S)
    if arr_match:
        try:
            result = json.loads(arr_match.group(1))
            print(f"DEBUG: Array regex match successful")
            return result
        except Exception as e:
            print(f"DEBUG: Array regex match failed: {e}")
            # Try to find a simpler array pattern
            simple_arr_match = re.search(r'(\[.*?\])', text, flags=re.S)
            if simple_arr_match:
                try:
                    result = json.loads(simple_arr_match.group(1))
                    print(f"DEBUG: Simple array regex match successful")
                    return result
                except Exception as e2:
                    print(f"DEBUG: Simple array regex match failed: {e2}")

    # Try to find JSON object
    obj_match = re.search(r'(\{.*?\})', text, flags=re.S)
    if obj_match:
        try:
            result = json.loads(obj_match.group(1))
            print(f"DEBUG: Object regex match successful")
            return result
        except Exception as e:
            print(f"DEBUG: Object regex match failed: {e}")

    # Try to find JSON after common prefixes like "Here is the JSON:" or "```json"
    json_patterns = [
        r'(?:Here is the JSON:|```json|JSON:|Output:)\s*(\[.*?\])',
        r'(?:Here is the JSON:|```json|JSON:|Output:)\s*(\{.*?\})',
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, text, flags=re.S | re.I)
        if match:
            try:
                result = json.loads(match.group(1))
                print(f"DEBUG: Pattern match successful")
                return result
            except Exception as e:
                print(f"DEBUG: Pattern match failed: {e}")
                continue

    print(f"DEBUG: All parsing attempts failed")
    return None
