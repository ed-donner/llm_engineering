# 🏭 Synthetic Dataset Generator
### *Structured JSON Data Generation using Hugging Face Inference API & Qwen2.5-72B-Instruct*

---

## 📘 Overview

A lightweight synthetic data generator that uses an LLM to produce structured JSON datasets representing **simple allocation problems**.  
Each generation produces N samples of **one dataset type** only:

| Type | Definition |
|------|-----------|
| `valid` | Allocations satisfy demand and do not exceed capacities |
| `demand_violation` | Total allocation is less than demand |
| `capacity_violation` | At least one supplier allocation exceeds its capacity |
| `borderline` | Allocations are exactly equal or very close to limits |

---

## 🎯 Objective

1. Learn how to use the **Hugging Face Inference API** (`InferenceClient`) for remote LLM inference.
2. Practice **prompt engineering** for structured JSON output.
3. Understand the difference between **local inference** (pipeline) and **remote inference** (API).

---

## 🧪 Model Selection Journey

| # | Model | Method | Result |
|---|-------|--------|--------|
| 1 | `HuggingFaceTB/SmolLM2-360M-Instruct` | `pipeline("text-generation")` | Only produced 1 sample, copied the system message example verbatim instead of generating new data. Too small (360M params) for structured JSON generation. |
| 2 | `Qwen/Qwen2.5-0.5B-Instruct` | `pipeline("text-generation")` | Kernel crashed — the model could not run locally on MacBook. Even at 0.5B parameters, local inference with `transformers` demands significant RAM/VRAM. |
| 3 | `Qwen/Qwen2.5-72B-Instruct` | `InferenceClient` (HF Inference API) | ✅ Works. Remote inference offloads computation to HF servers. The 72B model is powerful enough to produce diverse, correctly structured JSON. |

**Key takeaway:** Small models struggle with structured output tasks. Remote inference via the HF Inference API lets you use large models without local hardware constraints.

---

## ⚙️ Setup

1. **Install dependencies:**
   ```bash
   pip install huggingface_hub python-dotenv
   ```

2. **Create a `.env` file** in the `LLM-hands-on-practices/` root directory:
   ```
   HF_TOKEN=hf_your_token_here
   ```
   Get your token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).

---

## 🧩 Project Structure

```
05_dataset_generator/
├── generator.py      # Main script — prompt building, API call, JSON parsing
├── requirements.txt  # Python dependencies
└── README.md
```

---

## 🔧 How It Works

1. **`build_messages()`** constructs a chat prompt with:
   - A system message enforcing JSON-only output
   - A user message with the dataset type definition and one example
2. **`generate_dataset()`** sends the prompt to the HF Inference API via `client.chat_completion()`
3. The response is stripped of any markdown code fences and parsed as JSON

---

## ▶️ Usage

```bash
python generator.py
```

Edit `dataset_type` and `n_samples` in the `__main__` block to generate different types:

```python
dataset_type = "capacity_violation"  # valid | demand_violation | capacity_violation | borderline
n_samples = 5
```

---

## 💬 Example Output

```json
[
  {
    "type": "valid",
    "capacities": {"S1": 400, "S2": 600},
    "demand": 700,
    "allocations": {"S1": 300, "S2": 400}
  },
  {
    "type": "valid",
    "capacities": {"S1": 800, "S2": 200},
    "demand": 900,
    "allocations": {"S1": 700, "S2": 200}
  }
]
```

---

## 🧠 Insights Gained

- **Model size matters for structured output** — 360M and 500M parameter models couldn't reliably produce valid JSON arrays with multiple diverse samples.
- **Local vs. remote inference** — `pipeline()` loads weights into local RAM/VRAM; `InferenceClient` sends API requests to HF's servers. This is the critical difference when hardware is limited.
- **Prompt engineering** — explicitly stating "no markdown, no explanation, just raw JSON" and providing a single example was enough to get consistent output from a capable model.

---

## 🚀 Future Extensions

- Add a **Gradio UI** for interactive dataset generation
- Add **validation logic** to verify generated samples match their type definitions
- Support **batch export** to `.json` or `.csv` files
- Experiment with different models and compare output quality

---

## 🏁 Author

**Khashayar Bayati, Ph.D.**  
GitHub: [github.com/Khashayarbayati1](https://github.com/Khashayarbayati1)
