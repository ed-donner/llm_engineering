# 🏥 AI Patient Diagnosis Generator

A Kaggle notebook that uses a locally quantized Llama 3.2 model to automatically generate medical diagnoses, medication recommendations, and doctor notes for synthetic patient data.

---

## Overview

This project demonstrates running a large language model locally on a GPU to process structured medical data. It generates synthetic patient records and uses Llama 3.2 3B Instruct to produce clinical assessments in structured JSON format.

---

## Features

- Generates synthetic patient data (age, gender, symptoms) using Faker
- Runs Llama 3.2 3B Instruct locally with 4-bit quantization (BitsAndBytes)
- Produces structured JSON output with diagnosis, medication, and doctor notes for each patient
- Merges LLM output back into the original patient records
- Streams model output in real time using TextStreamer

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Model | Meta Llama 3.2 3B Instruct |
| Quantization | BitsAndBytes 4-bit (NF4) |
| Framework | HuggingFace Transformers |
| Data Generation | Faker |
| Platform | Kaggle (GPU T4) |
| Language | Python |

---

## How It Works

1. **Generate synthetic patients** — creates 5 patient records with random age, gender, and symptoms using Faker and UUID
2. **Load quantized model** — loads Llama 3.2 3B in 4-bit NF4 quantization to fit in GPU memory
3. **Build prompt** — formats all patient records into a single structured prompt
4. **Run inference** — model generates diagnosis, medication, and doctor notes for each patient in JSON format
5. **Parse and merge** — extracts the JSON array from the output and merges it back into the original patient records

---

## Setup

### Requirements
- Kaggle account with GPU enabled (Settings → Accelerator → GPU T4)
- HuggingFace account with access to Llama 3.2
- HuggingFace token saved as Kaggle secret (`HF_TOKEN`)

### Installation
```python
!pip install -q --upgrade bitsandbytes accelerate faker transformers
```

### HuggingFace Access
1. Request access to `meta-llama/Llama-3.2-3B-Instruct` on HuggingFace
2. Add your HF token to Kaggle Secrets as `HF_TOKEN`

---

## Sample Output

```json
{
  "patient_id": "f4a12edd-0a0a-44d8-aa36-a570b4a48867",
  "age": 60,
  "gender": "Male",
  "symptoms": ["chest pain", "shortness of breath"],
  "diagnosis": "Acute coronary syndrome",
  "medication": [
    {"name": "Aspirin", "dosage": "81mg"},
    {"name": "Beta blockers", "dosage": "25mg"}
  ],
  "doctor_notes": "Monitor for signs of myocardial infarction, consider revascularization if necessary."
}
```

---

## Notes

- This is a demonstration project only — outputs should never be used for actual medical decisions
- Batch size can be adjusted to process larger datasets
- For production scale, consider using vLLM for higher throughput