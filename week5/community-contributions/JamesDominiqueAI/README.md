Regulatory Compliance RAG
A retrieval-augmented generation (RAG) system for querying financial regulatory documents via a chat interface.
What it does

Chat — Ask questions about regulations (REG-ABC-2021/2023, REG-XYZ-2022, amendments, audit reports) and get cited answers
Evaluation — Measures retrieval quality (MRR, nDCG) and answer quality (accuracy, completeness, relevance) across 10 test cases
Adaptive retrieval — Rewrites queries and widens search scope automatically when confidence is low

Clone the repo and install dependencies: pip install -r requirements.txt
Copy .env.example to .env and fill in your API key + choose a model
Build the index: python app.py --ingest
Run the app: python app.py → opens at http://127.0.0.1:7860

Recommended model (free)
envOPENROUTER_API_KEY=your-key-here
MODEL=openrouter/google/gemini-2.0-flash-001
Get a free key at openrouter.ai
Dataset
The synthetic regulatory documents and evaluation tests used in this project are publicly available on Hugging Face.

Dataset: https://huggingface.co/datasets/dondodoai/regulatory-rag-data
Knowledge base: https://huggingface.co/datasets/dondodoai/regulatory-rag-data/tree/main/knowledge-base
Evaluation tests: https://huggingface.co/datasets/dondodoai/regulatory-rag-data/blob/main/evaluation/tests.jsonl

To use the dataset, download and place the files as follows:
- `knowledge-base/` folder → place in the root of the project next to `app.py`
- `evaluation/tests.jsonl` → place inside the `evaluation/` folder


All documents are synthetically generated. The regulations, institutions, and figures are fictional and for testing purposes only.