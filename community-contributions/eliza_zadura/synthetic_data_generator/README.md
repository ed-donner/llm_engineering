# Synthetic Test Data Generator

Week 3 course project — generate realistic JSON payloads for REST APIs using local LLMs.

## What it does

Takes an OpenAPI specification, extracts request body schemas, and uses quantized language models to generate synthetic test data that conforms to those schemas.

## How it works

1. Parse an OpenAPI spec (JSON) and extract endpoint schemas
2. Resolve `$ref` references to get flat JSON Schema definitions
3. Build a prompt from the schema and send it to a local 4-bit quantized model
4. Extract JSON from the model's response and validate it against the original schema

## Models compared

| Model | Params | Valid JSON | Schema Match | Notes |
| :-------: | :--------: | :-----------: | :--------------: | :-------: |
| Llama 3.1 8B Instruct | 8B | Yes | Yes | Best results — clean arrays, correct structure |
| Qwen 2.5 Coder 7B Instruct | 7B | Yes | Yes | Concise single-object output |
| Phi 4 Mini Instruct | 3.8B | Yes | No | Echoes schema definition, nests data under `"data"` key |

All models quantized to 4-bit (NF4) via BitsAndBytes. Tested with a minimal prompt (no few-shot examples).

## Setup

Requires an NVIDIA GPU with CUDA support. Install CUDA-enabled PyTorch first, then dependencies without resolving torch:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install --no-deps accelerate bitsandbytes transformers huggingface_hub[hf_xet]
```

Needs a Hugging Face token in `.env` as `HF_TOKEN` (Llama requires access approval).

## Files

- `JSON_for_REST.ipynb` — main notebook
- `storefront-sample.json` — sample OpenAPI spec (e-commerce storefront)
- `synthetic_data_generator_plan.md` — phased project plan
