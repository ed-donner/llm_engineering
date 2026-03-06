"""Run week1 day1 notebook code cells."""
import json
import os
import sys
from pathlib import Path

# Run from project root; week1 must be on path for scraper import
project_root = Path(__file__).resolve().parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root / "week1"))

# Minimal OpenAI client using requests (works with Python 3.6, no openai pkg needed)
import requests
class _Choice:
    def __init__(self, content): self.message = type('M', (), {'content': content})()
class _Response:
    def __init__(self, content): self.choices = [_Choice(content)]
class _ChatCompletions:
    def create(self, model, messages): 
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages}, timeout=60)
        r.raise_for_status()
        return _Response(r.json()["choices"][0]["message"]["content"])
class _OpenAI:
    def __init__(self): self.chat = type('C', (), {'completions': _ChatCompletions()})()
_openai_mod = type(sys)("openai")
_openai_mod.OpenAI = _OpenAI
sys.modules["openai"] = _openai_mod

# Mock IPython.display for non-notebook execution
def _display(x): print(x) if x is not None else None
def _markdown(x): return x
ipd = type(sys)("IPython.display")
ipd.display = _display
ipd.Markdown = _markdown
sys.modules["IPython"] = type(sys)("IPython")
sys.modules["IPython.display"] = ipd

nb_path = project_root / "week1" / "day1.ipynb"
with open(nb_path, encoding="utf-8") as f:
    nb = json.load(f)

cells = [
    "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
    for c in nb["cells"]
    if c["cell_type"] == "code"
]

g = {}
for i, code in enumerate(cells):
    if not code.strip():
        continue
    try:
        exec(code, g)
    except Exception as e:
        print(f"Cell {i+1} error: {e}", file=sys.stderr)
        raise

print("\n✓ Day 1 notebook completed successfully.")
