# Car Dataset Generator

This app generates text dataset files for car models from different brands using an LLM.
It also generates separate brand files.


## Setup

From `aryaman/dataset_generator`:

The script reads environment variables from `aryaman/.env` (already copied).

For OpenAI-compatible usage, the main client import is already set up through `../client.py`.
For local Ollama usage, you can switch to `../ollama_client.py` with a one-line import change.

## Run

```bash
python3 generate_car_dataset.py
```

Example commands:

```bash
# Generate 100 car files + matching brand files
python3 generate_car_dataset.py --count 100

# Generate only 25 cars
python3 generate_car_dataset.py --count 25

# Regenerate everything even if files already exist
python3 generate_car_dataset.py --count 100 --overwrite

# Custom output folders
python3 generate_car_dataset.py --count 40 --output-dir ./dataset_cars --brand-output-dir ./dataset_brands

# Run with more parallel threads
python3 generate_car_dataset.py --count 100 --workers 10
```

Optional flags:

- `--count 100`: number of car datasets to generate (1 to 100)
- `--overwrite`: regenerate files even if they already exist
- `--max-retries 3`: retry attempts per car
- `--delay-seconds 2`: base backoff delay
- `--workers 6`: parallel threads for API execution
- `--output-dir /path/to/dataset`: custom output location
- `--brand-output-dir /path/to/brands`: custom brand output location

## Build QA JSONL

After you generate the car and brand `.txt` files, you can build a sample-style QA JSONL file:

```bash
python3 build_jsonl_dataset.py
```

Example commands:

```bash
# Build the default QA dataset file at ../car_qa_dataset.jsonl
python3 build_jsonl_dataset.py

# Use custom source folders
python3 build_jsonl_dataset.py --cars-dir ./dataset_cars --brands-dir ./dataset_brands

# Write the QA JSONL to a custom output file
python3 build_jsonl_dataset.py --qa-output ../custom_car_qa.jsonl
```

What this tool does:

- reads each generated `.txt` file
- extracts only facts explicitly written in those files
- creates QA rows in the same shape as `../sample.jsonl`
- validates that each `reference_answer` is present in the original source text

That last validation step is the main safeguard that keeps the JSONL grounded in the generated dataset.

Important:

- `build_jsonl_dataset.py` is deterministic and does not call any LLM client.
- It does not use `client.py` or `ollama_client.py`.
- The only script that uses an LLM client is `generate_car_dataset.py`.

## Ollama
Recommended Ollama environment variables:

- `OLLAMA_BASE_URL`: default is `http://127.0.0.1:11434`
- `OLLAMA_MODEL`: example `llama3.1:8b`
- `OLLAMA_USER`: optional request user label

Notes:

- `ollama_client.py` exposes the same `load_client()` pattern and a compatible `client.responses.create(...)` call shape.
- It is intended to let you swap imports without rewriting the generator logic.
- Native tool-calling is not implemented in this adapter, but plain prompt/response generation works.

## Output

Expected output is `count` car text files in `dataset/`, for example:

- `toyota_corolla.txt`
- `honda_civic.txt`
- `ford_mustang.txt`

And separate brand files in `dataset/brands/`, for example:

- `toyota.txt`
- `honda.txt`
- `ford.txt`
