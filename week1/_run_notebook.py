"""Run a Jupyter notebook by executing its code cells."""
import json
import subprocess
import sys
from pathlib import Path

def run_notebook(notebook_path):
    nb_path = Path(notebook_path)
    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)
    
    code_cells = [
        "".join(c["source"])
        for c in nb["cells"]
        if c["cell_type"] == "code"
    ]
    
    globals_dict = {"__name__": "__main__"}
    
    for i, code in enumerate(code_cells):
        if not code.strip():
            continue
        # Handle shell commands (!cmd)
        lines = code.split("\n")
        exec_lines = []
        for line in lines:
            if line.strip().startswith("!"):
                cmd = line.strip()[1:].strip()
                print(f"\n>>> Running: {cmd}")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=nb_path.parent)
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)
                if result.returncode != 0:
                    print(f"Command failed with code {result.returncode}", file=sys.stderr)
            else:
                exec_lines.append(line)
        
        if exec_lines:
            exec_code = "\n".join(exec_lines)
            try:
                result = exec(exec_code, globals_dict)
                if result is not None:
                    print(result)
            except Exception as e:
                print(f"Cell {i+1} error: {e}", file=sys.stderr)
                raise

if __name__ == "__main__":
    run_notebook(Path(__file__).parent / "day2.ipynb")
