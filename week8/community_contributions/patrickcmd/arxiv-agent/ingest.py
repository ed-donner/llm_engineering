import os
import base64
from pathlib import Path
from datetime import datetime
from multiprocessing import Pool

import arxiv
from openai import OpenAI
from mistralai import Mistral
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from chromadb import PersistentClient
from tqdm import tqdm
from litellm import completion
from tenacity import retry, wait_exponential


load_dotenv(override=True)

MODEL = "openai/gpt-4.1-mini"
DB_NAME = str(Path(__file__).parent / "arxiv_db")
COLLECTION_NAME = "arxiv_papers"
EMBEDDING_MODEL = "text-embedding-3-large"
AVERAGE_CHUNK_SIZE = 500
WORKERS = 3
WAIT = wait_exponential(multiplier=1, min=10, max=240)

openai_client = OpenAI()
mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ArxivDocument(BaseModel):
    title: str
    authors: list[str]
    summary: str
    published: datetime
    updated: datetime
    pdf_url: str
    arxiv_url: str
    primary_category: str
    categories: list[str]
    doi: str | None = None
    comment: str | None = None
    journal_ref: str | None = None
    document_markdown: str = ""

    class Config:
        arbitrary_types_allowed = True


class Result(BaseModel):
    page_content: str
    metadata: dict


class Chunk(BaseModel):
    headline: str = Field(
        description="A brief heading for this chunk that captures the key topic"
    )
    summary: str = Field(
        description="A few sentences summarizing this chunk to answer common questions"
    )
    original_text: str = Field(
        description="The original text of this chunk from the paper, exactly as is"
    )

    def as_result(self, doc: ArxivDocument) -> Result:
        metadata = {
            "title": doc.title,
            "authors": ", ".join(doc.authors),
            "arxiv_url": doc.arxiv_url,
            "source": doc.pdf_url,
            "doi": doc.doi or "N/A",
            "primary_category": doc.primary_category,
            "published": doc.published.isoformat(),
        }
        page_content = self.headline + "\n\n" + self.summary + "\n\n" + self.original_text
        return Result(page_content=page_content, metadata=metadata)


class Chunks(BaseModel):
    chunks: list[Chunk]


# ---------------------------------------------------------------------------
# Step 1 — Fetch arxiv documents
# ---------------------------------------------------------------------------


def fetch_arxiv_documents(topic: str, k: int = 5) -> list[ArxivDocument]:
    """Search arXiv and return structured documents."""
    client = arxiv.Client()
    search = arxiv.Search(
        query=topic,
        max_results=k,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    documents = []
    for result in client.results(search):
        doc = ArxivDocument(
            title=result.title,
            authors=[a.name for a in result.authors],
            summary=result.summary,
            published=result.published,
            updated=result.updated,
            pdf_url=result.pdf_url,
            arxiv_url=result.entry_id,
            primary_category=result.primary_category,
            categories=result.categories,
            doi=result.doi,
            comment=result.comment,
            journal_ref=result.journal_ref,
        )
        documents.append(doc)

    print(f"Fetched {len(documents)} papers from arXiv for topic: '{topic}'")
    return documents


# ---------------------------------------------------------------------------
# Step 2 — Convert PDFs to markdown via Mistral OCR
# ---------------------------------------------------------------------------


def pdf_to_markdown(pdf_url: str) -> str:
    """Use Mistral OCR to extract markdown from an arXiv PDF URL."""
    response = mistral_client.ocr.process(
        model="mistral-ocr-latest",
        document={"type": "document_url", "document_url": pdf_url},
    )
    pages = [page.markdown for page in response.pages]
    return "\n\n".join(pages)


def enrich_documents(documents: list[ArxivDocument]) -> list[ArxivDocument]:
    """Download and OCR each paper's PDF, storing the markdown on the document."""
    for doc in tqdm(documents, desc="OCR processing PDFs"):
        try:
            doc.document_markdown = pdf_to_markdown(doc.pdf_url)
        except Exception as e:
            print(f"OCR failed for '{doc.title}': {e}")
            doc.document_markdown = doc.summary
    return documents


# ---------------------------------------------------------------------------
# Step 3 — LLM-based chunking
# ---------------------------------------------------------------------------


def _make_chunk_prompt(doc: ArxivDocument) -> str:
    how_many = (len(doc.document_markdown) // AVERAGE_CHUNK_SIZE) + 1
    return f"""You take an academic paper and split it into overlapping chunks for a knowledge base.

Paper title: {doc.title}
Authors: {', '.join(doc.authors)}
Category: {doc.primary_category}

A chatbot will use these chunks to answer questions about this paper and its topic.
Divide the document so the entire content is covered — don't leave anything out.
Target at least {how_many} chunks, but use more or fewer as appropriate.
Use roughly 25% overlap (~50 words) between adjacent chunks for best retrieval.

For each chunk provide:
- headline: a brief heading capturing the key topic
- summary: a few sentences summarising the chunk
- original_text: the exact text from the paper

Here is the paper content:

{doc.document_markdown}

Respond with the chunks."""


def _make_messages(doc: ArxivDocument) -> list[dict]:
    return [{"role": "user", "content": _make_chunk_prompt(doc)}]


@retry(wait=WAIT)
def process_document(doc: ArxivDocument) -> list[Result]:
    """Send a document to the LLM for chunking and return Results."""
    messages = _make_messages(doc)
    response = completion(model=MODEL, messages=messages, response_format=Chunks)
    reply = response.choices[0].message.content
    doc_chunks = Chunks.model_validate_json(reply).chunks
    return [chunk.as_result(doc) for chunk in doc_chunks]


def create_chunks(documents: list[ArxivDocument]) -> list[Result]:
    """Create chunks from all documents using parallel workers."""
    chunks: list[Result] = []
    with Pool(processes=WORKERS) as pool:
        for result in tqdm(
            pool.imap_unordered(process_document, documents),
            total=len(documents),
            desc="Chunking papers",
        ):
            chunks.extend(result)
    return chunks


# ---------------------------------------------------------------------------
# Step 4 — Embed and store in ChromaDB
# ---------------------------------------------------------------------------


def create_embeddings(chunks: list[Result]):
    """Embed chunks and store them in a persistent ChromaDB collection."""
    chroma = PersistentClient(path=DB_NAME)
    if COLLECTION_NAME in [c.name for c in chroma.list_collections()]:
        chroma.delete_collection(COLLECTION_NAME)

    texts = [c.page_content for c in chunks]

    # Embed in batches of 100 to stay within API limits
    all_vectors = []
    for i in range(0, len(texts), 100):
        batch = texts[i : i + 100]
        emb = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=batch).data
        all_vectors.extend([e.embedding for e in emb])

    collection = chroma.get_or_create_collection(COLLECTION_NAME)
    ids = [str(i) for i in range(len(chunks))]
    metas = [c.metadata for c in chunks]
    collection.add(ids=ids, embeddings=all_vectors, documents=texts, metadatas=metas)

    print(f"Vectorstore created with {collection.count()} chunks")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import sys

    topic = sys.argv[1] if len(sys.argv) > 1 else "transformer neural networks"
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    documents = fetch_arxiv_documents(topic, k)
    documents = enrich_documents(documents)
    chunks = create_chunks(documents)
    create_embeddings(chunks)
    print("Ingestion complete")