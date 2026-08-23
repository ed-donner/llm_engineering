"""
app.py - Kenya Legal Assistant RAG App
A demo showcasing the full RAG pipeline:
  1. Ingest: load → chunk → embed → store in ChromaDB
  2. Query: enrich question → embed → retrieve → rerank → generate answer

Usage:
  1. Set OPENAI_API_KEY in .env
  2. Run: python ingest.py   (once, to populate the vector DB)
  3. Run: python app.py
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple

import gradio as gr
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_core.documents import Document

from ingest import ingest as ingest_docs

load_dotenv()

# ─── Config ────────────────────────────────────────────────────────────────
CHROMA_DIR         = "./chroma_db"
EMBEDDING_MODEL    = "text-embedding-3-large"
LLM_MODEL          = "gpt-4o-mini"
CHUNK_SIZE         = 800
CHUNK_OVERLAP      = 150
RETRIEVAL_TOP_K    = 8     # how many chunks to retrieve
RERANK_TOP_N       = 4     # how many to keep after reranking
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
os.environ["OPENAI_API_KEY"] = openrouter_api_key
openrouter_base_url = "https://openrouter.ai/api/v1"


# ─── Step 1: Load vector store ──────────────────────────────────────────────
def get_vectorstore() -> Chroma | None:
    if not os.path.exists(CHROMA_DIR):
        return None
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=openrouter_api_key, base_url=openrouter_base_url)
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
        collection_name="kenya_legal_docs"
    )


# ─── Step 2: Enrich the question ────────────────────────────────────────────
def enrich_question(original_query: str, llm: ChatOpenAI) -> str:
    """
    Use the LLM to rewrite and expand the query for better retrieval.
    Technique: HyDE-style — generate a hypothetical answer to use as search query.
    """
    prompt = f"""You are a Kenyan legal expert. A law student has asked:

"{original_query}"

Your task:
1. Rewrite the question to be more precise and use proper legal terminology.
2. Add relevant Kenyan legal concepts, statutes, or case references that would help find an answer.
3. Return ONLY the enriched query as a single paragraph. Do not answer the question.

Enriched query:"""

    response = llm.invoke(prompt)
    return response.content.strip()


# ─── Step 3: Retrieve relevant chunks ──────────────────────────────────────
def retrieve_chunks(
    original_query: str,
    enriched_query: str,
    vectorstore: Chroma,
    top_k: int = RETRIEVAL_TOP_K
) -> List[Document]:
    """Retrieve chunks using both original and enriched query, deduplicate."""
    seen_ids = set()
    all_chunks = []

    for query in [original_query, enriched_query]:
        results = vectorstore.similarity_search(query, k=top_k // 2)
        for doc in results:
            uid = doc.page_content[:100]  
            if uid not in seen_ids:
                seen_ids.add(uid)
                all_chunks.append(doc)

    return all_chunks


# ─── Step 4: Rerank chunks ──────────────────────────────────────────────────
def rerank_chunks(
    original_query: str,
    chunks: List[Document],
    llm: ChatOpenAI,
    top_n: int = RERANK_TOP_N
) -> List[Document]:
    """
    Ask the LLM to score each chunk's relevance to the query,
    then return the top_n most relevant chunks.
    """
    if not chunks:
        return []

    # Build scoring prompt
    chunk_list = "\n\n".join([
        f"[CHUNK {i+1}]\n{doc.page_content}"
        for i, doc in enumerate(chunks)
    ])

    prompt = f"""You are a Kenyan legal expert. Score each chunk below on its relevance to the query.
Return ONLY a JSON array of integers (scores 1–10), one per chunk, in order.
Example for 3 chunks: [8, 3, 7]

QUERY: {original_query}

CHUNKS:
{chunk_list}

SCORES (JSON array only):"""

    try:
        response = llm.invoke(prompt)
        raw = response.content.strip()
        # Extract the JSON array robustly
        start = raw.find("[")
        end = raw.rfind("]") + 1
        scores = json.loads(raw[start:end])
        # Sort chunks by score descending, take top_n
        scored = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_n]]
    except Exception:
        # Fallback: return first top_n chunks as-is
        return chunks[:top_n]


# ─── Step 5: Generate final answer ─────────────────────────────────────────
def generate_answer(
    original_query: str,
    top_chunks: List[Document],
    llm: ChatOpenAI
) -> Tuple[str, str]:
    """
    Build system prompt with retrieved context + user prompt with original query.
    Returns (answer, sources_text).
    """
    context = "\n\n---\n\n".join([
        f"[Source: {doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}"
        for doc in top_chunks
    ])

    system_prompt = f"""You are KenyaLex, an expert legal assistant specializing in Kenyan law.
You assist law students at Kenyan universities with questions on constitutional law,
contract law, criminal law, and land/property law.

INSTRUCTIONS:
- Answer based on the provided legal context below.
- Cite specific Articles, Sections, Acts, or Cases when relevant.
- Structure your answer clearly with headings if needed.
- If the context doesn't fully cover the question, say so honestly and note what additional research the student should do.
- Use plain, educational language suitable for a law student.
- Always reference Kenyan law specifically (Constitution 2010, Kenyan statutes, eKLR cases).

LEGAL CONTEXT:
{context}
"""

    user_prompt = f"Please answer this question: {original_query}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    response = llm.invoke(messages)
    answer = response.content.strip()

    # Build sources summary
    sources = list(set([doc.metadata.get("source", "Unknown") for doc in top_chunks]))
    sources_text = "📚 **Sources used:** " + " | ".join(sources)

    return answer, sources_text


# ─── Full RAG Pipeline ──────────────────────────────────────────────────────
def run_rag_pipeline(query: str, show_steps: bool = False) -> Tuple[str, str]:
    """
    Orchestrates the full pipeline and returns (answer, pipeline_trace).
    """
    if not query.strip():
        return "Please enter a question.", ""

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return "⚠️ OPENAI_API_KEY not set. Add it to your .env file.", ""

    vectorstore = get_vectorstore()
    if vectorstore is None:
        return (
            "⚠️ No documents ingested yet. Run `python ingest.py` first, "
            "or upload documents in the 'Upload Documents' tab.",
            ""
        )

    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.1, api_key=openrouter_api_key, base_url=openrouter_base_url)
    trace_lines = []

    # Step 1: Enrich
    trace_lines.append("**Step 1 — Enriching query with LLM...**")
    enriched = enrich_question(query, llm)
    trace_lines.append(f"> {enriched}\n")

    # Step 2: Retrieve
    trace_lines.append(f"**Step 2 — Retrieving top {RETRIEVAL_TOP_K} chunks from ChromaDB...**")
    chunks = retrieve_chunks(query, enriched, vectorstore, top_k=RETRIEVAL_TOP_K)
    trace_lines.append(f"> Retrieved {len(chunks)} unique chunks\n")

    # Step 3: Rerank
    trace_lines.append(f"**Step 3 — Reranking with LLM, keeping top {RERANK_TOP_N}...**")
    top_chunks = rerank_chunks(query, chunks, llm, top_n=RERANK_TOP_N)
    trace_lines.append(f"> Reranked to {len(top_chunks)} most relevant chunks\n")

    # Step 4: Generate
    trace_lines.append("**Step 4 — Generating answer...**")
    answer, sources = generate_answer(query, top_chunks, llm)
    trace_lines.append(sources)

    full_answer = f"{answer}\n\n{sources}"
    pipeline_trace = "\n".join(trace_lines)

    return full_answer, pipeline_trace


# ─── Upload and Ingest User Documents ───────────────────────────────────────
def ingest_uploaded_files(files) -> str:
    """Ingest user-uploaded PDF or TXT files into ChromaDB via ingest.py."""
    if not files:
        return "No files uploaded."

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return "⚠️ OPENAI_API_KEY not set."

    all_docs = []
    loaded_names = []

    for file in files:
        fp = file.name
        ext = Path(fp).suffix.lower()
        fname = Path(fp).name

        try:
            if ext == ".pdf":
                loader = PyPDFLoader(fp)
            elif ext == ".txt":
                loader = TextLoader(fp, encoding="utf-8")
            else:
                continue

            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = fname
            all_docs.extend(docs)
            loaded_names.append(f"✓ {fname} ({len(docs)} doc(s))")
        except Exception as e:
            loaded_names.append(f"✗ {fname}: {str(e)}")

    if not all_docs:
        return "No valid documents were processed."

    chunks, source_summaries = ingest_docs(docs=all_docs)
    summary = "\n".join(source_summaries)
    return f"✅ Ingested {len(chunks)} chunks from {len(source_summaries)} file(s):\n\n{summary}"


# ─── Gradio UI ──────────────────────────────────────────────────────────────
EXAMPLE_QUESTIONS = [
    "What are the fundamental rights under the Kenyan Constitution that cannot be limited?",
    "What elements are required for a valid contract under Kenyan law?",
    "What is the punishment for robbery with violence under the Penal Code?",
    "How does adverse possession work in Kenya and what is the required time period?",
    "What did the Supreme Court decide in the Muruatetu case about the death penalty?",
    "What are a spouse's rights to matrimonial property after divorce in Kenya?",
    "What constitutes misrepresentation in Kenyan contract law and what remedies are available?",
    "Explain the three categories of land ownership under the Kenyan Constitution.",
]

CSS = """
.gradio-container { font-family: 'Georgia', serif !important; }
.main-header {
    background: linear-gradient(135deg, #1a3a2a 0%, #2d5a3d 50%, #1a3a2a 100%);
    padding: 24px 32px;
    border-radius: 12px;
    margin-bottom: 20px;
    border: 1px solid #4a8a5a;
}
.main-header h1 { color: #f0e8d0; margin: 0; font-size: 1.8rem; }
.main-header p  { color: #b8d4c0; margin: 6px 0 0; font-size: 0.95rem; }
.pipeline-box { background: #f8f4ec; border-left: 4px solid #2d5a3d; padding: 12px; border-radius: 6px; font-size: 0.85rem; }
footer { display: none !important; }
"""

def build_ui():
    with gr.Blocks(css=CSS, title="KenyaLex — Legal AI Assistant") as demo:

        gr.HTML("""
        <div class="main-header">
          <h1>⚖️ KenyaLex — AI Legal Assistant</h1>
          <p>Powered by RAG · Specialised in Kenyan Constitutional, Contract, Criminal & Land Law</p>
        </div>
        """)

        with gr.Tabs():

            # ── Tab 1: Ask a Question ────────────────────────────────
            with gr.TabItem("💬 Ask a Question"):
                with gr.Row():
                    with gr.Column(scale=3):
                        question_input = gr.Textbox(
                            label="Your Legal Question",
                            placeholder="e.g. What rights cannot be limited under the Kenyan Constitution?",
                            lines=3,
                        )
                        with gr.Row():
                            submit_btn = gr.Button("⚖️ Get Legal Answer", variant="primary", size="lg")
                            clear_btn = gr.Button("Clear", size="lg")

                        show_pipeline = gr.Checkbox(
                            label="Show RAG pipeline trace (for learning purposes)",
                            value=True
                        )

                        gr.Examples(
                            examples=EXAMPLE_QUESTIONS,
                            inputs=question_input,
                            label="📖 Example Questions",
                        )

                    with gr.Column(scale=4):
                        answer_output = gr.Markdown(
                            label="Answer",
                            value="*Your answer will appear here...*"
                        )

                with gr.Accordion("🔍 RAG Pipeline Trace", open=False):
                    pipeline_output = gr.Markdown(
                        value="*Pipeline steps will appear here after you ask a question.*",
                        elem_classes=["pipeline-box"]
                    )

                def answer_question(query, show_steps):
                    answer, trace = run_rag_pipeline(query, show_steps)
                    return answer, trace

                submit_btn.click(
                    fn=answer_question,
                    inputs=[question_input, show_pipeline],
                    outputs=[answer_output, pipeline_output],
                )
                clear_btn.click(
                    fn=lambda: ("", "*Your answer will appear here...*", ""),
                    outputs=[question_input, answer_output, pipeline_output]
                )

            # ── Tab 2: Upload Your Documents ─────────────────────────
            with gr.TabItem("📁 Upload Your Documents"):
                gr.Markdown("""
### Add Your Own Legal Documents
Upload your own case studies, lecture notes, statutes, or any legal PDFs/TXTs.
They will be chunked, embedded, and added to the knowledge base — then you can ask questions about them.
                """)
                file_upload = gr.File(
                    label="Upload PDF or TXT files",
                    file_count="multiple",
                    file_types=[".pdf", ".txt"],
                )
                ingest_btn = gr.Button("📥 Ingest Documents", variant="primary")
                ingest_output = gr.Textbox(label="Ingestion Result", lines=6)

                ingest_btn.click(
                    fn=ingest_uploaded_files,
                    inputs=[file_upload],
                    outputs=[ingest_output]
                )

            # ── Tab 3: About the RAG Pipeline ────────────────────────
            with gr.TabItem("🧠 How It Works"):
                gr.Markdown("""
## The RAG Pipeline Explained

This app demonstrates a **production-grade RAG (Retrieval-Augmented Generation)** pipeline:

---

### 📥 Ingestion (Run Once)
1. **Load** — Documents are loaded from a folder (`.txt`, `.pdf`)
2. **Chunk** — Text is split into overlapping chunks (800 tokens, 150 overlap) using `RecursiveCharacterTextSplitter`
3. **Encode** — Each chunk is encoded using OpenAI `text-embedding-3-large`
4. **Store** — Vectors are persisted in **ChromaDB** (local vector database)

---

### 💬 Query (Every Question)
1. **Enrich Question** — The LLM rewrites and expands your question using legal terminology (HyDE-style)
2. **Dual Retrieval** — Both original + enriched queries search ChromaDB for the top-K most similar chunks
3. **Rerank** — The LLM scores each retrieved chunk for relevance; top-N are selected
4. **Generate** — Chunks are concatenated into a `system_prompt`; your original question becomes the `user_prompt`; the LLM generates a cited answer

---

### 🛠️ Tech Stack
| Component | Tool |
|-----------|------|
| Vector DB | ChromaDB |
| Embeddings | OpenAI text-embedding-3-large |
| LLM | GPT-4o-mini |
| Orchestration | LangChain |
| UI | Gradio |

---

### 📚 Built-In Knowledge Base
- **Constitution of Kenya 2010** — Bill of Rights, Executive, Judiciary
- **Contract Law** — Elements, breach, remedies, key cases (eKLR)
- **Penal Code** — Murder, manslaughter, robbery, sexual offences
- **Land Law** — Land Act 2012, Land Registration Act, adverse possession
                """)

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
