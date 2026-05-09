# Data for Mini RAG (AI Articles)

The data for this project is **not stored in the repo**. Download it from Google Drive and place it in this folder (`tope-ai-labs`) before running the notebook.

## What you need

- **`knowledge_base/`** — Folder of markdown articles about AI (required). The notebook loads and chunks these to build the RAG index.
- **`chroma_ai_articles/`** — Optional pre-built ChromaDB vector store. If you skip this, the notebook will create it from `knowledge_base/` when you run it (takes a few minutes).

## Download instructions

### Option A: Download from Google Drive (manual)

1. Open the data archive on Google Drive:  
   **[Download: tope-ai-labs-data.zip](https://drive.google.com/)** *(replace with your actual shareable link)*

2. Download **tope-ai-labs-data.zip** to your machine.

3. Extract the zip **into this folder** (`week5/community-contributions/tope-ai-labs/`) so that you have:
   ```
   tope-ai-labs/
   ├── knowledge_base/          ← required
   │   ├── what_is_ai.md
   │   ├── large_language_models.md
   │   ├── retrieval_augmented_generation.md
   │   ├── transformers_and_attention.md
   │   └── embeddings_and_vector_stores.md
   ├── chroma_ai_articles/     ← optional (notebook can build it)
   ├── mini_rag_ai_articles.ipynb
   └── ...
   ```

4. Open and run `mini_rag_ai_articles.ipynb`.

### Option B: Download with a script (if link is set up)

If the maintainer has shared the file with a direct-download link or file ID, you can use the helper script:

```bash
pip install gdown
python download_data.py
```

Then run the notebook. Edit `download_data.py` if you have a different Google Drive file ID or URL.

---

## For maintainers: hosting the data on Google Drive

1. Zip the `knowledge_base/` folder (and optionally `chroma_ai_articles/`) into **tope-ai-labs-data.zip**.
2. Upload the zip to Google Drive.
3. Right‑click the file → **Share** → set to “Anyone with the link” (viewer) → copy link.
4. Put the shareable link in this file under **Option A** above, and if using a direct file ID, set it in `download_data.py` (see script comments).
