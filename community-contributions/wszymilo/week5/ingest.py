"""
Ingestion: load .docx/.pdf/.txt from paths, LLM chunking (300–400 chars, 50 overlap),
unique chunk IDs, FAISS index under temp dir.
"""

import uuid
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from litellm import completion
from pydantic import BaseModel, Field

from config import (
    CHUNK_MAX_CHARS,
    CHUNK_OVERLAP_CHARS,
    EMBEDDING_MODEL,
    LLM_MODEL,
    FAISS_INDEX_DIR,
)

ALLOWED_EXTENSIONS = {".docx", ".pdf", ".txt"}


class ChunkSchema(BaseModel):
    """Single chunk from LLM: headline, summary, original text."""

    headline: str = Field(description="Brief heading for this chunk, a few words")
    summary: str = Field(description="A few sentences summarizing the chunk")
    original_text: str = Field(
        description="Original text of this chunk from the document, unchanged"
    )


class ChunksSchema(BaseModel):
    """Multiple chunks from one document."""

    chunks: list[ChunkSchema]


def _loader_for_path(path: str):
    path_lower = path.lower()
    if path_lower.endswith(".pdf"):
        return PyPDFLoader(path)
    if path_lower.endswith(".docx") or path_lower.endswith(".doc"):
        return Docx2txtLoader(path)
    if path_lower.endswith(".txt"):
        return TextLoader(path, encoding="utf-8")
    return None


def load_documents_from_paths(file_paths: list[str]) -> list[Document]:
    """Load .docx, .pdf, .txt files into LangChain Documents."""
    documents = []
    for path in file_paths:
        ext = Path(path).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue
        loader = _loader_for_path(path)
        if loader is None:
            continue
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = path
            documents.append(doc)
    return documents


def _chunking_prompt(source: str, text: str) -> str:
    return f"""Split this document into overlapping chunks for a knowledge base.

Rules:
- Each chunk must be at most {CHUNK_MAX_CHARS} characters in total (headline + summary + original_text).
- Consecutive chunks must overlap by about {CHUNK_OVERLAP_CHARS} characters so the same content can appear in adjacent chunks.
- Cover the entire document; do not leave anything out.
- For each chunk provide: a short headline, a brief summary, and the exact original text of that chunk.

Source: {source}

Document text:

{text}

Respond with the chunks in JSON format: {{"chunks": [{{"headline": "...", "summary": "...", "original_text": "..."}}, ...]}}"""


def chunk_document_with_llm(doc: Document) -> list[Document]:
    """Use LLM to split one document into multiple chunks (300–400 chars, 50 overlap)."""
    prompt = _chunking_prompt(doc.metadata.get("source", ""), doc.page_content)
    response = completion(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format=ChunksSchema,
    )
    content = response.choices[0].message.content
    parsed = ChunksSchema.model_validate_json(content)
    out = []
    for c in parsed.chunks:
        page_content = f"{c.headline}\n\n{c.summary}\n\n{c.original_text}"
        out.append(
            Document(
                page_content=page_content,
                metadata={
                    "source": doc.metadata.get("source", ""),
                    "chunk_id": str(uuid.uuid4()),
                },
            )
        )
    return out


def assign_sequential_ids(chunks: list[Document]) -> None:
    """Assign stable sequential chunk_id for rerank (1-based in prompts)."""
    for i, doc in enumerate(chunks):
        doc.metadata["chunk_id"] = str(i + 1)


def run_ingestion(
    temp_dir: str,
    progress_callback=None,
) -> str:
    """
    Load all .docx/.pdf/.txt from temp_dir, chunk with LLM, build FAISS, save under temp_dir.
    progress_callback(progress: float, desc: str) with progress in [0, 1].
    Returns path to FAISS index directory. Raises if no valid files.
    """
    def report(p: float, msg: str):
        if progress_callback:
            progress_callback(p, msg)

    temp_path = Path(temp_dir)
    file_paths = []
    for ext in ALLOWED_EXTENSIONS:
        file_paths.extend(temp_path.glob(f"*{ext}"))
    file_paths = [str(p) for p in file_paths]
    if not file_paths:
        raise ValueError("No .docx, .pdf, or .txt files found in the upload directory.")

    report(0.0, "Loading files…")
    raw_docs = load_documents_from_paths(file_paths)
    if not raw_docs:
        raise ValueError("No content could be loaded from the selected files.")

    report(0.05, f"Loaded {len(raw_docs)} documents. Chunking…")
    all_chunks = []
    n_docs = len(raw_docs)
    for i, doc in enumerate(raw_docs):
        # Chunking: 0.05 -> 0.75 (70% of bar)
        p = 0.05 + 0.70 * (i + 1) / n_docs
        report(p, f"Chunking document {i + 1}/{n_docs}…")
        chunk_list = chunk_document_with_llm(doc)
        all_chunks.extend(chunk_list)

    assign_sequential_ids(all_chunks)

    report(0.80, "Building FAISS index…")
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = FAISS.from_documents(all_chunks, embeddings)
    faiss_index_path = temp_path / FAISS_INDEX_DIR
    faiss_index_path.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(faiss_index_path))

    report(1.0, "Ingestion complete.")
    return str(faiss_index_path)


def load_vectorstore(faiss_index_path: str) -> FAISS:
    """Load FAISS vectorstore from directory (e.g. under temp dir)."""
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    return FAISS.load_local(
        faiss_index_path,
        embeddings,
        allow_dangerous_deserialization=True,
    )
