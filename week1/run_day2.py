"""Run week1 day2 notebook code cells."""
import json
import os
import subprocess
import sys
from pathlib import Path

# Run from project root
project_root = Path(__file__).resolve().parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root / "week1"))

# OpenAI-compatible client using requests (supports OpenAI, Gemini, Ollama)
import requests
from requests.exceptions import HTTPError, ConnectionError

class _Choice:
    def __init__(self, content): self.message = type('M', (), {'content': content})()

class _Response:
    def __init__(self, content): self.choices = [_Choice(content)]

def _chat_create(base_url, api_key, model, messages):
    url = base_url.rstrip("/") + "/chat/completions" if not base_url.endswith("completions") else base_url
    r = requests.post(url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": messages}, timeout=120)
    r.raise_for_status()
    return _Response(r.json()["choices"][0]["message"]["content"])

class _ChatCompletions:
    def __init__(self, base_url, api_key):
        self._base = base_url.rstrip("/")
        self._key = api_key
    def create(self, model, messages):
        return _chat_create(self._base, self._key, model, messages)

class _OpenAI:
    def __init__(self, base_url=None, api_key=None):
        self._base = base_url or "https://api.openai.com/v1"
        self._key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.chat = type('C', (), {'completions': _ChatCompletions(self._base, self._key)})()

_openai_mod = type(sys)("openai")
_openai_mod.OpenAI = _OpenAI
sys.modules["openai"] = _openai_mod

# Load notebook
nb_path = project_root / "week1" / "day2.ipynb"
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
    run_lines = []
    for line in code.split("\n"):
        if line.strip().startswith("!"):
            cmd = line.strip()[1:].strip()
            print(f"\n>>> Running: {cmd}")
            subprocess.run(cmd, shell=True, cwd=str(project_root))
        else:
            run_lines.append(line)
    if run_lines:
        try:
            exec("\n".join(run_lines), g)
        except (KeyError, HTTPError, ConnectionError) as e:
            print(f"Cell {i+1}: Skipping ({type(e).__name__}): {str(e)[:80]}...", file=sys.stderr)
        except Exception as e:
            print(f"Cell {i+1} error: {e}", file=sys.stderr)
            raise

print("\nDay 2 notebook completed.")
