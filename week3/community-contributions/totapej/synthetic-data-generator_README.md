# Synthetic Data Generator

A Python notebook that generates fictional tabular datasets using **Qwen2.5-1.5B-Instruct** from Hugging Face. A Gradio interface lets you describe a dataset, define its columns, preview generated records, and download the results.

The default example creates product reviews. Change the description, schema, and instructions to generate other datasets, such as support tickets or sample business records.

## Features

- Configurable dataset descriptions and JSON Schemas.
- Validation of required fields, data types, ranges, and allowed values.
- Removal of exact duplicate records.
- Adjustable row count, temperature, and random seed.
- Dataset preview, generation report, and raw-response inspection.
- CSV and JSON exports with generation metadata.

## Requirements

- A Python notebook environment with a CUDA-enabled GPU.
- PyTorch with CUDA support.
- Internet access for downloading dependencies and model weights.

Install the remaining dependencies in a notebook cell:

```python
%pip install "transformers" "gradio==6.29.0" "jsonschema>=4.23,<5" pandas
```

## Usage

1. Run the notebook cells in order to load the model and launch the interface.
2. Describe the dataset and provide a valid JSON Schema.
3. Add instructions for the desired content and relationships between fields.
4. Set the row count, temperature, and seed.
5. Click **Generate dataset**.
6. Review the accepted records and generation report, then download the files.

Start with a small dataset, such as 12 rows, before requesting more records.

## Schema Configuration

Define between 1 and 8 columns using `string`, `integer`, `number`, or `boolean` types. List every column in `required` and set `additionalProperties` to `false`.

The schema textbox requires JSON: use double quotes, lowercase `true`/`false`, and no trailing commas. To convert a Python schema dictionary:

```python
print(json.dumps(schema_dictionary, indent=2))
```

## How It Works

The model generates JSON arrays of up to three records per batch. The application parses each response, validates individual records, removes exact duplicates, and retries within a fixed limit.

Generation stops when the requested count is reached or the retry budget is exhausted. Partial results are explicitly marked **Incomplete**.

## Output Files

| File | Contents |
| --- | --- |
| `synthetic_data.csv` | Accepted records in tabular format. |
| `synthetic_data.json` | Accepted records as a JSON array. |
| `generation_metadata.json` | Model information, schema, instructions, settings, and generation counters. |

## Limitations

Schema validation checks structure, not semantic correctness. Review generated labels and relationships before using the data. Realistic distributions, balanced classes, and paraphrase-level uniqueness are not guaranteed.

This project is intended for testing and prototyping; generated data should not replace real-world evaluation.
