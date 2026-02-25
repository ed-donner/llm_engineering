"""
Ingest LiteLLM documentation from knowledge-base/ into Chroma: LLM-based chunking,
OpenAI text-embedding-3-small embeddings, PersistentClient. Load .env from repo root.
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

from chromadb import PersistentClient
from litellm import completion
from openai import OpenAI
from pydantic import BaseModel, Field
from tenacity import retry, wait_exponential
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent
DB_NAME = str(PROJECT_ROOT / "vector_db")
COLLECTION_NAME = "docs"
KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "knowledge-base"
EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_MODEL = "openai/gpt-4o-mini"
AVERAGE_CHUNK_SIZE = 800
WORKERS = 8  # Increase if no rate limits; set to 1 if you hit limits
WAIT = wait_exponential(multiplier=1, min=4, max=120)

client = OpenAI()


class Result(BaseModel):
    """Single chunk with content and metadata for Chroma."""

    page_content: str
    metadata: dict


class Chunk(BaseModel):
    """One chunk produced by the LLM: headline, summary, original text."""

    headline: str = Field(
        description="A brief heading for this chunk, likely to be matched by a query",
    )
    summary: str = Field(
        description="A few sentences summarizing the content to answer common questions",
    )
    original_text: str = Field(
        description="The original text of this chunk from the document, unchanged",
    )

    def as_result(self, document: dict) -> Result:
        metadata = {"source": document["source"], "type": document["type"]}
        content = f"{self.headline}\n\n{self.summary}\n\n{self.original_text}"
        return Result(page_content=content, metadata=metadata)


class Chunks(BaseModel):
    chunks: list[Chunk]


def fetch_documents() -> list[dict]:
    """Load all .md and .mdx files from knowledge-base/, grouped by top-level folder (type)."""
    documents = []
    if not KNOWLEDGE_BASE_PATH.is_dir():
        print(f"Knowledge base not found: {KNOWLEDGE_BASE_PATH}. Run scripts/build_knowledge_base.py first.")
        return documents
    for folder in sorted(KNOWLEDGE_BASE_PATH.iterdir()):
        if not folder.is_dir():
            continue
        doc_type = folder.name
        for ext in ("*.md", "*.mdx"):
            for file in folder.rglob(ext):
                try:
                    text = file.read_text(encoding="utf-8", errors="replace")
                except Exception as e:
                    print(f"Skip {file}: {e}")
                    continue
                documents.append({
                    "type": doc_type,
                    "source": file.as_posix(),
                    "text": text,
                })
    print(f"Loaded {len(documents)} documents from {KNOWLEDGE_BASE_PATH}")
    return documents


def make_prompt(document: dict) -> str:
    n = max(1, len(document["text"]) // AVERAGE_CHUNK_SIZE)
    return f"""You split a document into overlapping chunks for a RAG knowledge base.

The document is from the LiteLLM documentation. Section: {document["type"]}. Source: {document["source"]}.

A chatbot will use these chunks to answer questions about LiteLLM. Split the document so the entire content is covered across chunks with some overlap (~25% or ~50 words). Aim for about {n} or more chunks. For each chunk provide: headline (short), summary (a few sentences), and original_text (exact copy of the segment). Respond with JSON chunks only.

Document:

{document["text"]}
"""


@retry(wait=WAIT)
def process_document(document: dict) -> list[Result]:
    """Chunk one document using the LLM and return list of Result for Chroma."""
    messages = [{"role": "user", "content": make_prompt(document)}]
    response = completion(
        model=CHUNK_MODEL,
        messages=messages,
        response_format=Chunks,
    )
    raw = response.choices[0].message.content
    parsed = Chunks.model_validate_json(raw)
    return [c.as_result(document) for c in parsed.chunks]


def create_chunks(documents: list[dict]) -> list[Result]:
    """Chunk all documents (sequential for stability; set WORKERS for parallel if needed)."""
    if WORKERS <= 1:
        chunks = []
        for doc in tqdm(documents, desc="Chunking"):
            chunks.extend(process_document(doc))
        return chunks
    from multiprocessing import Pool
    chunks = []
    with Pool(processes=WORKERS) as pool:
        for result in tqdm(
            pool.imap_unordered(process_document, documents),
            total=len(documents),
            desc="Chunking",
        ):
            chunks.extend(result)
    return chunks


def create_embeddings(chunks: list[Result]) -> None:
    """Embed all chunk texts with OpenAI and upsert into Chroma."""
    if not chunks:
        print("No chunks to embed. Skipping.")
        return
    chroma = PersistentClient(path=DB_NAME)
    if COLLECTION_NAME in [c.name for c in chroma.list_collections()]:
        chroma.delete_collection(COLLECTION_NAME)
    texts = [c.page_content for c in chunks]
    # Batch to avoid token limits (e.g. 8k tokens per request)
    batch_size = 100
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        all_embeddings.extend(e.embedding for e in resp.data)
    ids = [str(i) for i in range(len(chunks))]
    metas = [c.metadata for c in chunks]
    coll = chroma.get_or_create_collection(COLLECTION_NAME)
    coll.add(ids=ids, embeddings=all_embeddings, documents=texts, metadatas=metas)
    print(f"Vector store created with {coll.count()} chunks at {DB_NAME}")


def main() -> None:
    documents = fetch_documents()
    if not documents:
        return
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete.")


if __name__ == "__main__":
    main()
