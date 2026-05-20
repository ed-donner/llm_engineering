# RAG vs Fine-Tuning (Company Policy QA)

This project compares three approaches for answering company-policy questions on the same dataset:

- Retrieval-Augmented Generation (RAG)
- Closed-source fine-tuning (`gpt-4.1-nano`)
- Open-source fine-tuning (`Llama-3.1-8B-Instruct`)

The workflow includes dataset preparation, vector database ingestion for RAG, response generation, and LLM-as-a-judge evaluation.

## Project Structure

- `_1__dataset_push_to_hub.ipynb`: dataset preparation and push to Hugging Face Hub
- `_2_1__rag_data_ingestion.py`: builds the Chroma vector store from the dataset
- `_2_2__rag_question_answering.py`: RAG answer generation function (`rag_answer`)
- `_3__gpt_4__1_nano_fine_tuning.py`: closed-source fine-tuning data prep + job creation
- `_4_llama_3__1_8B_instruct_fine_tuning.ipynb`: open-source fine-tuning workflow
- `_5__test_response_generation.ipynb`: generates model responses on test set
- `_6__evaluation.ipynb`: evaluates outputs on completeness, relevance, and correctness
- `jsonl/`: train/validation fine-tuning files
- `responses/`: generated model outputs for each approach
- `chroma_langchain_db/`: persisted Chroma vector DB for RAG
- `ipynb_files/`: earlier notebook versions and experiments

## Dataset

The project uses:

- `ayanmukherjee/repliqa-4-company-policies-answerable`

This dataset is a derived version of the ServiceNow RepliQA dataset's `repliqa_4` split.
From that split, this project uses the documents related to company policies.

Loaded in code via:

```python
from datasets import load_dataset
ds = load_dataset("ayanmukherjee/repliqa-4-company-policies-answerable")
```

## Prerequisites

- Python 3.10+
- A virtual environment (recommended)
- Access tokens/API keys:
  - Hugging Face token (`HF_TOKEN`)
  - OpenAI API key (`OPENAI_API_KEY`)

Install dependencies from the repository root:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file (or export variables in your shell):

```bash
HF_TOKEN=your_huggingface_token
OPENAI_API_KEY=your_openai_api_key
```

Most scripts call `load_dotenv(override=True)`, so `.env` is picked up automatically.

## End-to-End Workflow

Run from this directory:

```bash
cd week8/community_contributions/ayan-rag-vs-finetuning
```

### 1) Build RAG index

```bash
python _2_1__rag_data_ingestion.py
```

This:

- loads dataset records
- chunks document text with `RecursiveCharacterTextSplitter`
- embeds chunks using `google/embeddinggemma-300m`
- writes vectors to `chroma_langchain_db`

### 2) Launch closed-source fine-tuning job

```bash
python _3__gpt_4__1_nano_fine_tuning.py
```

This script:

- creates `jsonl/fine_tune_train.jsonl` and `jsonl/fine_tune_validation.jsonl`
- uploads both files to OpenAI
- starts a fine-tuning job on `gpt-4.1-nano-2025-04-14`

After completion, copy your fine-tuned model ID and update it in `_5__test_response_generation.ipynb`.

### 3) Run open-source fine-tuning

Use notebook:

- `_4_llama_3__1_8B_instruct_fine_tuning.ipynb`

This part is notebook-driven (typically run in Colab/GPU environment).

### 4) Generate test responses

Run notebook:

- `_5__test_response_generation.ipynb`

It produces:

- `responses/rag_responses.jsonl`
- `responses/closed_source_responses.jsonl`
- `responses/open_source_responses.jsonl` (if open-source model run is completed)

### 5) Evaluate all techniques

Run notebook:

- `_6__evaluation.ipynb`

Evaluation uses an LLM judge with three metrics:

- correctness
- completeness
- relevance

In the current checked-in run, RAG has the best aggregate scores among the compared approaches.

## Notes

- Response generation/evaluation in notebooks currently evaluate 66 test cases for consistency with the open-source fine-tuning run.
- If you re-run ingestion, the existing Chroma collection is deleted and recreated.
- Fine-tuning and judge calls are paid API operations; monitor usage before large-scale runs.

## Quick Start

```bash
cd week8/community_contributions/ayan-rag-vs-finetuning
python _2_1__rag_data_ingestion.py
python _3__gpt_4__1_nano_fine_tuning.py
# then run _5__test_response_generation.ipynb and _6__evaluation.ipynb
```
