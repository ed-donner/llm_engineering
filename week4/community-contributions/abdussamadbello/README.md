## Week 4 – Python to Go (Golang) code converter (abdussamadbello)

Week 4 code generator: **Python → Go** instead of Python→C++. A frontier model converts a Python snippet into idiomatic Golang.

The notebook `week4-assignment.ipynb`:
- Defines a system prompt for “Python → idiomatic Go” (preserve logic, use Go conventions).
- `python_to_go(python_code)` calls `gpt-4o-mini` and returns the generated Go code.
- Runs on one example (a small `fib` function) and prints the Go output.

### How to run

1. Add `OPENAI_API_KEY` to your `.env` (do not commit it).
2. Open `week4-assignment.ipynb` and run all cells.
3. Optionally change `example_python` to another snippet and re-run the last cell.

In the local planning notebook you can also call the same logic with Ollama (`use_ollama=True`) to compare outputs.
