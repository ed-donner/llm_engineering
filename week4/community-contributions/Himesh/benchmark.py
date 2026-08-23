"""
Benchmark: Port Python → C++ via LLMs and compare execution times.

Usage in notebook:
    from benchmark import benchmark_models
    
    models = {
        "GPT-5 Nano":       "openai/gpt-5-nano",
        "Claude 3.5 Haiku": "anthropic/claude-3.5-haiku",
    }
    results = benchmark_models(openrouter, models, pi, compile_command, run_command, system_info=system_info)
"""

import hashlib
import io
import os
import re
import subprocess
import sys
import time


# ── Prompts ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
Your task is to convert Python code into high performance C++ code.
Respond only with C++ code. Do not provide any explanation other than occasional comments.
The C++ response needs to produce an identical output in the fastest possible time.
"""


def _user_prompt(python: str, system_info: dict, compile_cmd: list[str]) -> str:
    return f"""
Port this Python code to C++ with the fastest possible implementation that produces identical output in the least time.
The system information is:
{system_info}
Your response will be written to a file called main.cpp and then compiled and executed; the compilation command is:
{compile_cmd}
Respond only with C++ code.
Python code to port:

```python
{python}
```
"""


# ── Python Baseline ─────────────────────────────────────────────────────────

def run_python(code: str) -> float:
    """Execute Python code, capture stdout, and parse the execution time.
    
    Returns execution time in seconds.
    Raises ValueError if time cannot be parsed from output.
    """
    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        exec(code, {"__builtins__": __builtins__})
    finally:
        sys.stdout = old_stdout

    output = captured.getvalue()
    print(output, end="")  # echo to notebook

    match = re.search(r"Execution Time:\s*([\d.]+)\s*seconds", output)
    if not match:
        raise ValueError(f"Could not parse execution time from Python output:\n{output}")
    return float(match.group(1))


# ── Helpers ──────────────────────────────────────────────────────────────────

def _file_hash(path: str) -> str:
    """Return MD5 hex digest of a file, or empty string if file doesn't exist."""
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


# ── Core Functions ───────────────────────────────────────────────────────────

def port(client, model: str, python: str, system_info: dict = None, compile_cmd: list[str] = None) -> dict:
    """Call LLM via streaming to port Python → C++.
    
    Returns dict with keys: cpp_code, ttft, generation_time, file_changed.
    Raises on any API error.
    """
    kwargs = {}
    
    kwargs["reasoning_effort"] = "high"

    old_hash = _file_hash("main.cpp")

    # Stream to measure TTFT and total generation time
    t_start = time.time()
    ttft = None
    chunks = []

    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(python, system_info or {}, compile_cmd or [])},
        ],
        stream=True,
        **kwargs,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            if ttft is None:
                ttft = time.time() - t_start
            chunks.append(delta.content)

    generation_time = time.time() - t_start

    cpp_code = "".join(chunks)
    cpp_code = cpp_code.replace("```cpp", "").replace("```", "").strip()

    if not cpp_code:
        raise ValueError(f"Model {model} returned empty response")

    with open("main.cpp", "w", encoding="utf-8") as f:
        f.write(cpp_code)

    new_hash = _file_hash("main.cpp")
    file_changed = new_hash != old_hash

    return {
        "cpp_code": cpp_code,
        "ttft": ttft or 0.0,
        "generation_time": generation_time,
        "file_changed": file_changed,
        "file_size": len(cpp_code),
    }


def compile_and_run(compile_cmd: list[str], run_cmd: list[str], runs: int = 3) -> dict:
    """Compile main.cpp, run it `runs` times, parse and return timing stats."""
    subprocess.run(compile_cmd, check=True, text=True, capture_output=True)

    times = []
    outputs = []
    for i in range(runs):
        result = subprocess.run(run_cmd, check=True, text=True, capture_output=True)
        outputs.append(result.stdout.strip())

        match = re.search(r"Execution Time:\s*([\d.]+)\s*seconds", result.stdout)
        if match:
            times.append(float(match.group(1)))

    return {
        "times": times,
        "avg": sum(times) / len(times) if times else None,
        "min": min(times) if times else None,
        "max": max(times) if times else None,
        "outputs": outputs,
    }


def port_and_benchmark(
    client, model: str, python: str, compile_cmd: list[str], run_cmd: list[str],
    system_info: dict = None, runs: int = 3
) -> dict:
    """Port Python→C++ via model, compile, run, and return benchmark results.
    
    Raises on API errors so stale main.cpp is never used.
    """
    print(f"🔄 Porting with {model}...")
    port_info = port(client, model, python, system_info, compile_cmd)

    print(f"   TTFT:       {port_info['ttft']:.2f}s")
    print(f"   Generation: {port_info['generation_time']:.2f}s")
    print(f"   File size:  {port_info['file_size']} bytes")
    if not port_info["file_changed"]:
        print("   ⚠️  WARNING: main.cpp content unchanged from previous model!")

    print(f"⚙️  Compiling & running {runs}x...")
    stats = compile_and_run(compile_cmd, run_cmd, runs)

    print(f"✅ {model}")
    for i, t in enumerate(stats["times"]):
        print(f"   Run {i+1}: {t:.6f}s")
    print(f"   Avg:   {stats['avg']:.6f}s")

    return {"model": model, **stats, **port_info}


# ── Multi-Model Comparison ───────────────────────────────────────────────────

def benchmark_models(
    client, models: dict[str, str], python: str,
    compile_cmd: list[str], run_cmd: list[str],
    system_info: dict = None, runs: int = 3
):
    """Run Python baseline, benchmark all models, and print a comparison table.
    
    Args:
        client:       OpenAI-compatible client
        models:       dict of {display_name: model_id}
        python:       Python source code to port
        compile_cmd:  Compilation command list
        run_cmd:      Run command list
        system_info:  System info dict (optional)
        runs:         Number of runs per model
    
    Returns:
        list of result dicts, sorted by avg time (fastest first)
    """
    # ── Python baseline ──
    print("🐍 Running Python baseline...")
    python_time = run_python(python)
    print(f"   Python time: {python_time:.6f}s\n")

    # ── Benchmark each model ──
    results = []
    for name, model_id in models.items():
        try:
            result = port_and_benchmark(client, model_id, python, compile_cmd, run_cmd, system_info, runs)
            result["name"] = name
            results.append(result)
        except Exception as e:
            print(f"❌ {name} ({model_id}) FAILED: {e}")
            results.append({"name": name, "model": model_id, "avg": None, "error": str(e)})
        print()

    # Sort by avg time (failures last)
    results.sort(key=lambda r: r["avg"] if r["avg"] is not None else float("inf"))

    # ── Summary table ──
    print("=" * 90)
    print(f"{'Rank':<5} {'Model':<30} {'Avg (s)':<12} {'Speedup':<10} {'TTFT':<10} {'Gen Time'}")
    print("-" * 90)
    for i, r in enumerate(results, 1):
        if r["avg"] is not None:
            speedup = python_time / r["avg"]
            ttft = f"{r.get('ttft', 0):.2f}s"
            gen = f"{r.get('generation_time', 0):.2f}s"
            print(f"{i:<5} {r['name']:<30} {r['avg']:<12.6f} {speedup:<10.0f}X {ttft:<10} {gen}")
        else:
            print(f"{i:<5} {r['name']:<30} {'FAILED':<12} {'-':<10} {'-':<10} -")
    print("=" * 90)
    print(f"Python baseline: {python_time:.6f}s")

    return results
