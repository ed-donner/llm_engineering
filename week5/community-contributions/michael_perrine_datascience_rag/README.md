# Data Science Docs RAG

RAG assistant over the official reference docs for pandas, NumPy, SciPy, scikit-learn, matplotlib and Plotly (1,030 PDF pages).

Live app: https://data-science-library.streamlit.app

- Ingestion: PyMuPDF, section/version metadata parsed from page headers, page-level chunks, text-embedding-3-large (1536-d) in Supabase pgvector with an HNSW index
- Answers: structured output; citations are built in code from metadata, not by the LLM
- Two refusal layers: similarity gate (0.40), then an LLM `in_context` check
- Evaluation (72 questions): hit@1 0.842, MRR 0.899, all 15 out-of-scope questions refused; page vs section chunking compared with a blind LLM judge

Files: `datascience_rag.ipynb` (build and evaluation), `rag.py` (pipeline), `app.py` (Streamlit chat with streaming).
Run: set `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, then `streamlit run app.py`. The PDFs and cached eval files are not included.
