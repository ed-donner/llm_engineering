# Synthetic Test Data Generator (Week 3 Project)

## Goal
Build a small system that generates synthetic JSON datasets for testing REST APIs. The generator should accept a specification (initially an OpenAPI document) and produce realistic example payloads for endpoints.

This project is also used to explore differences between LLMs, quantization levels, and prompting approaches.

---

# Phase 1 — Minimal Generator

## 1. Input
- Start with **OpenAPI specification (YAML/JSON)**
- Extract:
  - endpoints
  - request bodies
  - response schemas

## 2. Schema Extraction
Write a parser that pulls out:
- object fields
- types
- constraints

Example schema output:

```
{
  "endpoint": "/users",
  "method": "POST",
  "fields": [
    {"name": "id", "type": "integer"},
    {"name": "email", "type": "string"},
    {"name": "createdAt", "type": "datetime"}
  ]
}
```

## 3. Prompt Builder
Convert extracted schema into prompt template.

Example:

"Generate 10 realistic JSON objects matching this schema..."

Include constraints:
- types
- formatting
- optional relationships

## 4. Model Execution
Run prompt against different models.

Example candidates:
- llama3
- qwen coder
- phi

Experiment with:
- quantized vs non‑quantized
- different sampling settings

## 5. Output
Save generated datasets as:

```
/data
  users.json
  orders.json
  products.json
```

---

# Phase 2 — Multi‑Model Comparison

Run same generation task across models.

Track:
- schema correctness
- realism of data
- formatting accuracy

Possible metrics:

| model | quant | valid JSON | schema match | realism |
|------|------|------|------|------|

---

# Phase 3 — Validation

Add automatic checks:

1. JSON validity
2. Schema conformity
3. Field constraints

Optional:
- JSONSchema validator
- custom rule checks

---

# Phase 4 — Extensions

Possible next improvements:

### More Inputs
- SQL schema
- GraphQL schema
- Example JSON

### Realism Improvements
- correlated fields
- realistic timestamps
- consistent IDs

### Prompt Improvements
- few‑shot examples
- chain‑of‑thought suppression

---

# Phase 5 — Notebook Workflow

Implement inside **Google Colab notebook**.

Cells:

1. Load OpenAPI
2. Extract schema
3. Build prompt
4. Run model
5. Validate output
6. Compare models

---

# Minimal Deliverable

Working notebook that:

1. Takes OpenAPI input
2. Generates JSON test data
3. Compares outputs from multiple models

Keep scope intentionally small for the assignment.

Extensions are optional.

