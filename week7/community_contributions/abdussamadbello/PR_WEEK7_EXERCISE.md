# Pull Request: Week 7 Exercise (abdussamadbello)

## Title (for GitHub PR)

**Week 7 Exercise: Multi-task (category + price), RAG comparison, and reasons (abdussamadbello)**

---

## Description

This PR adds my **Week 7 Exercise** to `week7/community_contributions/abdussamadbello/`. It extends the “Price is Right” capstone with the **same Week 7 model** (QLoRA Llama):

1. **Multi-task**: Predict **category + price** in one completion (`Category: X. Price is $Y.00`).
2. **RAG**: Retrieve similar products (sentence-transformers), add to prompt; **compare** pricer-only vs pricer+RAG (MAE).
3. **Reasons**: One-sentence explanation (“Why might this product cost around $X?”) via same model or API.

### Author

**Abdussamad Bello** (abdussamadbello)

---

## What's in this submission

| Item | Description |
|------|-------------|
| **multitask_data.py** | Multi-task prompt/completion format and parsing (category + price). |
| **rag_retriever.py** | RAG index over train items; `format_similar_products(query, k)` for prompt context. |
| **reasons.py** | `get_reason()` — same-model second prompt or API (e.g. GPT-4o-mini). |
| **week7-multitask-prompt-data.ipynb** | Build multi-task dataset from Hub items; optional push to Hub. |
| **week7-eval-multitask-rag-reasons.ipynb** | Load adapter; multi-task predictor; pricer_only vs pricer_with_rag; reasons sample. |
| **README.md** | Setup, what’s included, how to run. |
| **CONTRIBUTION_PLAN.md** | Plan and checklist for this contribution. |
| **PR_WEEK7_EXERCISE.md** | This PR description (copy-paste into GitHub). |

### Features

- **Multi-task**: Single completion format `Category: <cat>. Price is $<num>.00`; parser for eval; dataset notebook for train/val/test.
- **RAG**: In-memory index (sentence-transformers/all-MiniLM-L6-v2); top-k similar products appended to prompt; eval compares MAE (pricer only vs pricer + RAG).
- **Reasons**: One-sentence “why ~$X?” using the fine-tuned model (second prompt) or LiteLLM/OpenAI.

---

## Technical notes

- **Paths**: Run notebooks from **repo root**; `week7` and `week7/community_contributions/abdussamadbello` are added to `sys.path` so `pricer` and local modules load.
- **Dependencies**: `python-dotenv`, `huggingface_hub`, `datasets`, `transformers` for data; for eval (GPU): `torch`, `peft`, `bitsandbytes`, `accelerate`, `sentence-transformers`; optional `litellm` for API reasons.
- **Env**: `HF_TOKEN` required; `OPENAI_API_KEY` optional for reasons.
- **Training**: Use official Week 7 Colab (Days 3–4) with the multi-task dataset; save adapter to Hub. No training code in this folder.

---

## Checklist

- [x] Changes are under `week7/community_contributions/abdussamadbello/`.
- [x] No edits to owner/main repo files outside this folder.
- [x] README describes setup and how to run.
- [ ] **Notebook outputs:** Clear outputs before merge if required by the repo.

---

## How to run

1. Set `HF_TOKEN` in `.env` at repo root.
2. **Multi-task data**: From repo root, open `week7/community_contributions/abdussamadbello/week7-multitask-prompt-data.ipynb`, run all cells. No GPU. Optionally set `MULTITASK_DATASET` to push to Hub.
3. **Training**: Use Week 7 Colab with the multi-task dataset; save adapter to Hub.
4. **Eval**: Open `week7-eval-multitask-rag-reasons.ipynb`, set `ADAPTER_PATH` to your adapter. Run; compare pricer-only vs pricer+RAG; view reasons sample. Requires GPU (or run in Colab).

Thanks for reviewing.
