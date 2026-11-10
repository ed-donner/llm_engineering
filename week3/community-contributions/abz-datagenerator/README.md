# AgriSynth

A synthetic data generator for Indonesian agriculture datasets. Write a short
description, review the generated schema, and get a ready-to-download dataset.
Built with Gradio and free Hugging Face models.

## Quick start (uv)

```bash
uv sync
export HF_TOKEN=hf_xxx   # PowerShell: $env:HF_TOKEN="hf_xxx"
uv run app.py            # opens at http://127.0.0.1:7860
```

Create a token at https://huggingface.co/settings/tokens. You can also paste it
into the token field in the UI instead of setting `HF_TOKEN`.

Run the offline smoke tests (no token needed): `uv run python tests/test_smoke.py`

## How it works

1. **Schema**: an LLM turns your short description into a JSON schema (fields,
   types, and variation attributes such as commodity or tone). You can edit it.
2. **Generate**: rows are produced in small batches. Each batch gets a different
   combination of variation attributes, chosen by code, to keep the data diverse.
3. **Validate and dedupe**: every row is type-checked against the schema, then
   exact and near-duplicates are removed.
4. **Export and evaluate**: view the table, download CSV or JSONL, and check
   the quality report (valid rate, duplicates, distributions).

## Project layout

| File | Purpose |
|---|---|
| `app.py` | Gradio UI (Schema, Generate, Evaluation tabs) |
| `generator.py` | LLM wrapper, schema validation, batch generation, dedup |
| `evaluator.py` | Quality summary |
| `presets.py` | Example agriculture dataset descriptions |
| `tests/test_smoke.py` | End-to-end test with a fake LLM |

## Notes

- Models are listed in `MODELS` in `generator.py`. Free-tier availability changes,
  so swap in another model ID if one fails. Llama models may require accepting
  their license on Hugging Face first.
- Start with 10 to 30 rows to check the valid rate before scaling up.
