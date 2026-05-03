# Day 5 Assignment Checklist: FinSynth Ledger Lab

## Goal

Build one Gradio app that generates synthetic finance datasets.

Core pipeline:

Open-source HuggingFace model -> rough JSON  
GPT/frontier model -> repair and validate JSON  
Python -> DataFrame and CSV  
Gradio -> user interface

Keep the project minimal.

Use:

- 1 notebook only
- Optional: 1 helper file only if absolutely needed
- No database
- No backend server
- No extra folders unless required by the notebook

Recommended structure:

- `finsynth-ledger-lab/`
  - `finsynth_ledger_lab.ipynb`
  - `.env` optional, only if running locally

Do not create multiple helper files unless the notebook becomes messy.

---

## Phase 1: Minimal Setup

### Feature

Set up the notebook and install the minimum packages needed.

### Checklist

- [ ] Create one notebook: `finsynth_ledger_lab.ipynb`
- [ ] Install required packages:
  - [ ] `gradio`
  - [ ] `pandas`
  - [ ] `openai`
  - [ ] `transformers`
  - [ ] `accelerate`
  - [ ] `bitsandbytes`
- [ ] Add OpenAI API key safely
- [ ] Decide how to handle HuggingFace model:
  - [ ] Assignment-compliant path: load model with `transformers`
  - [ ] Optional testing path: HuggingFace `InferenceClient`
- [ ] Keep all main functions inside the notebook

### Test

- [ ] Notebook runs from top to bottom without import errors
- [ ] API keys are loaded without being hard-coded in visible code
- [ ] You can print a simple test message from the notebook

---

## Phase 2: Dataset Presets

### Feature

Create 3 fixed dataset presets. Do not build custom schemas in v1.

### Preset 1: Personal Bank Statement

Schema:

| Field         | Meaning              |
| ------------- | -------------------- |
| `date`        | Transaction date     |
| `working`     | Debit or Credit      |
| `description` | Merchant and purpose |
| `withdrawal`  | Money spent          |
| `deposit`     | Money received       |
| `balance`     | Running balance      |

### Checklist

- [ ] Create bank statement prompt template
- [ ] Include salary, groceries, food, transport, subscriptions, transfers, refunds
- [ ] Require JSON only
- [ ] Require running balance to update correctly
- [ ] Limit generated rows to user-selected row count

### Test

- [ ] Prompt can generate 5 fake bank-statement rows
- [ ] Output contains only the required fields
- [ ] Output does not contain real account numbers or personal data

### Preset 2: Credit Card Spending Log

Schema:

| Field          | Meaning              |
| -------------- | -------------------- |
| `date`         | Spending date        |
| `description`  | Merchant and purpose |
| `amount_spent` | Amount charged       |

### Checklist

- [ ] Create credit-card spending prompt template
- [ ] Include restaurants, transport, subscriptions, online shopping, groceries
- [ ] Require JSON only
- [ ] Keep schema simple

### Test

- [ ] Prompt can generate 5 fake credit-card rows
- [ ] Output contains only `date`, `description`, and `amount_spent`
- [ ] Amounts are numeric

### Preset 3: Company Expense Ledger

Schema:

| Field          | Meaning                     |
| -------------- | --------------------------- |
| `date`         | Expense date                |
| `description`  | Vendor and business purpose |
| `amount_spent` | Expense amount              |

### Checklist

- [ ] Create company expense prompt template
- [ ] Include SaaS, office supplies, travel, meals, vendor payments
- [ ] Require fake company/vendor-style data
- [ ] Require JSON only

### Test

- [ ] Prompt can generate 5 fake company-expense rows
- [ ] Output contains only `date`, `description`, and `amount_spent`
- [ ] Output looks like business expense data, not personal spending data

---

## Phase 3: Open-Source Model Draft Generator

### Feature

Use an open-source HuggingFace model to generate rough JSON.

Recommended model:

`Qwen/Qwen2.5-72B-Instruct`

Optional heavier model:

`Qwen/Qwen2.5-7B-Instruct`

### Checklist

- [ ] Load one open-source model
- [ ] Use HuggingFace inference api, using the InferenceClient
- [ ] Create function: `generate_raw_json(prompt, temperature, max_tokens)`
- [ ] Return raw model text
- [ ] Print raw output for comparison
- [ ] Start with 5 rows only

### Test

- [ ] Open-source model generates text from a prompt
- [ ] Model can attempt JSON output
- [ ] Raw output is visible before GPT repair
- [ ] Generation works for at least one dataset preset

---

## Phase 4: GPT Repair and Validation

### Feature

Use GPT/frontier model to repair rough open-source output into clean JSON.

### Checklist

- [ ] Create function: `repair_json_with_gpt(raw_text, dataset_type)`
- [ ] GPT receives:
  - [ ] raw open-source model output
  - [ ] selected dataset type
  - [ ] required schema
- [ ] GPT returns valid JSON only
- [ ] GPT removes markdown, explanations, and extra text
- [ ] GPT enforces correct fields
- [ ] GPT fixes obvious balance errors for bank statements
- [ ] GPT avoids real personal data

### Test

- [ ] Give GPT messy JSON-like text
- [ ] GPT returns parseable JSON
- [ ] `json.loads()` works on the repaired output
- [ ] Repaired output follows the selected schema

---

## Phase 5: JSON to DataFrame to CSV

### Feature

Convert repaired JSON into a table and downloadable CSV.

### Checklist

- [ ] Create function: `json_to_dataframe(clean_json)`
- [ ] Parse JSON with `json.loads()`
- [ ] Convert list of dictionaries into `pandas.DataFrame`
- [ ] Create function: `save_csv(df)`
- [ ] Save CSV as `synthetic_finance_data.csv`
- [ ] Return:
  - [ ] DataFrame preview
  - [ ] cleaned JSON text
  - [ ] CSV file path
  - [ ] warning message if parsing fails

### Test

- [ ] Repaired JSON converts into a DataFrame
- [ ] DataFrame has correct columns
- [ ] CSV file is created
- [ ] CSV can be opened and read correctly

---

## Phase 6: Gradio UI

### Feature

Create a simple UI for non-technical users.

### Inputs

- [ ] Dataset type dropdown:
  - [ ] Personal bank statement
  - [ ] Credit card spending log
  - [ ] Company expense ledger
- [ ] Row count slider: 5 to 50
- [ ] Temperature slider: 0.2 to 1.0
- [ ] Prompt textbox
- [ ] GPT repair checkbox
- [ ] Generate button

### Outputs

- [ ] DataFrame preview
- [ ] Final repaired JSON textbox
- [ ] CSV download file
- [ ] Warning/status message
- [ ] Optional raw open-source output textbox

### Test

- [ ] Selecting a dataset type updates the prompt textbox
- [ ] Clicking generate runs the full pipeline
- [ ] DataFrame appears in the UI
- [ ] JSON appears in the UI
- [ ] CSV download works
- [ ] Raw open-source output is visible if included

---

## Phase 7: Prompt Variety Requirement

### Feature

Prove that the app uses a variety of prompts.

### Checklist

- [ ] Bank statement prompt exists
- [ ] Credit-card log prompt exists
- [ ] Company expense ledger prompt exists
- [ ] Each prompt has a different schema
- [ ] Each prompt has different generation rules
- [ ] User can edit the prompt before generation
- [ ] Temperature slider changes output diversity

### Test

- [ ] Generate one dataset from each preset
- [ ] Confirm each output has a different schema
- [ ] Confirm edited prompt changes the output
- [ ] Confirm higher temperature creates more varied descriptions

---

## Phase 8: Raw vs Repaired Comparison

### Feature

Show the trade-off between open-source and closed-source models.

### Checklist

- [ ] Display raw open-source output
- [ ] Display GPT-repaired output
- [ ] Show final DataFrame from repaired output
- [ ] Add short explanation in notebook:
  - [ ] Open-source model generates cheaper rough data
  - [ ] GPT improves JSON validity and consistency
  - [ ] Combined pipeline gives better structured output

### Test

- [ ] Raw output and repaired output are both visible
- [ ] Differences are easy to compare
- [ ] Repaired output is more structured than raw output

---

## Phase 9: Final Assignment Evidence

### Feature

Make sure the notebook clearly proves every hard requirement.

### Checklist

- [ ] Add markdown section: project pitch
- [ ] Add markdown section: model roles
- [ ] Add markdown section: prompt variety
- [ ] Add markdown section: Gradio UI explanation
- [ ] Add markdown section: limitations
- [ ] Add markdown section: future improvements

### Test

- [ ] A reviewer can understand the project by reading the notebook
- [ ] The notebook shows both model roles clearly
- [ ] The notebook has screenshots or visible Gradio output if needed
- [ ] The project can be demoed in under 3 minutes

---

## Definition of Done

| Requirement                       | Proof                                    | Done |
| --------------------------------- | ---------------------------------------- | ---- |
| Generates synthetic data          | App outputs fake finance datasets        | [ ]  |
| Uses open-source model            | HuggingFace model generates rough JSON   | [ ]  |
| Uses closed-source/frontier model | GPT repairs and validates JSON           | [ ]  |
| Uses variety of prompts           | 3 preset prompts plus editable textbox   | [ ]  |
| Has Gradio UI                     | User can generate data without coding    | [ ]  |
| Outputs structured data           | JSON, DataFrame, and CSV are produced    | [ ]  |
| CSV download works                | Gradio returns downloadable CSV file     | [ ]  |
| Shows model trade-off             | Raw output vs repaired output comparison | [ ]  |
| Avoids real sensitive data        | Prompts require fake synthetic data only | [ ]  |
| Bonus: 4-bit quantization         | `bitsandbytes` NF4 used                  | [ ]  |

---

## Recommended Build Order

1. Create one notebook.
2. Write one hard-coded bank-statement prompt.
3. Generate 5 rows with open-source model.
4. Print raw output.
5. Send raw output to GPT for repair.
6. Parse repaired JSON.
7. Convert JSON to DataFrame.
8. Save CSV.
9. Wrap pipeline in Gradio.
10. Add 3 dataset presets.
11. Add prompt auto-fill.
12. Add raw vs repaired output display.
13. Add 4-bit quantization if time allows.
14. Add final explanation markdown.

---

## Do Not Build in V1

- [ ] Custom schema builder
- [ ] User accounts
- [ ] Database storage
- [ ] Charts
- [ ] Authentication
- [ ] Real bank statement upload
- [ ] Fine-tuning
- [ ] 1000-row generation
- [ ] Multi-agent workflow
- [ ] Multiple helper files
- [ ] Separate backend server

---

## Final Scope

Build only this:

- 3 fixed finance dataset presets
- Open-source rough JSON generation
- GPT JSON repair and validation
- DataFrame preview
- CSV download
- Gradio UI
- Raw vs repaired comparison
- Optional 4-bit quantization

That is enough for the assignment.
