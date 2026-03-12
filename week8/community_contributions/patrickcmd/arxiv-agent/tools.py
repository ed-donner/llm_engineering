import json
import re
from pathlib import Path

import arxiv
from openai import OpenAI
from dotenv import load_dotenv
from chromadb import PersistentClient
from tqdm import tqdm

from ingest import (
    ArxivDocument,
    Result,
    pdf_to_markdown,
    process_document,
)

load_dotenv(override=True)

DB_NAME = str(Path(__file__).parent / "arxiv_db")
COLLECTION_NAME = "arxiv_papers"
EMBEDDING_MODEL = "text-embedding-3-large"

openai_client = OpenAI()


def search_knowledge_base(query: str, k: int = 10) -> list[Result]:
    """Embed the query and retrieve the top-k chunks from ChromaDB."""
    chroma = PersistentClient(path=DB_NAME)
    collection = chroma.get_or_create_collection(COLLECTION_NAME)

    if collection.count() == 0:
        return []

    query_vec = (
        openai_client.embeddings.create(model=EMBEDDING_MODEL, input=[query])
        .data[0]
        .embedding
    )
    n = min(k, collection.count())
    results = collection.query(query_embeddings=[query_vec], n_results=n)

    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append(Result(page_content=doc, metadata=meta))
    return chunks


def search_arxiv_papers(query: str, max_results: int = 5) -> list[dict]:
    """Search arXiv for papers and return structured summaries."""
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = []
    for result in client.results(search):
        papers.append(
            {
                "title": result.title,
                "authors": [a.name for a in result.authors],
                "summary": result.summary,
                "arxiv_url": result.entry_id,
                "pdf_url": result.pdf_url,
                "primary_category": result.primary_category,
                "published": result.published.isoformat(),
            }
        )
    return papers


def _extract_arxiv_ids(urls: list[str]) -> list[str]:
    """Pull arXiv numeric IDs out of URLs or bare IDs."""
    ids = []
    for url in urls:
        m = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", url)
        if m:
            ids.append(m.group(1))
    return ids


def ingest_papers(arxiv_urls: list[str]) -> str:
    """Fetch, OCR, chunk, embed and store papers identified by URL/ID."""
    ids = _extract_arxiv_ids(arxiv_urls)
    if not ids:
        return "No valid arXiv IDs found in the provided URLs."

    client = arxiv.Client()
    search = arxiv.Search(id_list=ids)

    documents: list[ArxivDocument] = []
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

    all_chunks: list[Result] = []
    for doc in tqdm(documents, desc="Ingesting papers"):
        try:
            doc.document_markdown = pdf_to_markdown(doc.pdf_url)
        except Exception:
            doc.document_markdown = doc.summary

        chunks = process_document(doc)
        all_chunks.extend(chunks)

    if not all_chunks:
        return "No chunks created from the provided papers."

    texts = [c.page_content for c in all_chunks]
    all_vectors: list[list[float]] = []
    for i in range(0, len(texts), 100):
        batch = texts[i : i + 100]
        emb = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=batch).data
        all_vectors.extend([e.embedding for e in emb])

    chroma = PersistentClient(path=DB_NAME)
    collection = chroma.get_or_create_collection(COLLECTION_NAME)
    offset = collection.count()
    new_ids = [str(offset + i) for i in range(len(all_chunks))]
    metas = [c.metadata for c in all_chunks]
    collection.add(
        ids=new_ids, embeddings=all_vectors, documents=texts, metadatas=metas
    )

    titles = [d.title for d in documents]
    return (
        f"Successfully ingested {len(documents)} paper(s) "
        f"({len(all_chunks)} chunks): {', '.join(titles)}"
    )


def get_paper_details(arxiv_url: str) -> dict:
    """Fetch full metadata for a single arXiv paper."""
    ids = _extract_arxiv_ids([arxiv_url])
    if not ids:
        return {"error": f"Could not extract arXiv ID from: {arxiv_url}"}

    client = arxiv.Client()
    search = arxiv.Search(id_list=ids[:1])

    for result in client.results(search):
        return {
            "title": result.title,
            "authors": [a.name for a in result.authors],
            "summary": result.summary,
            "arxiv_url": result.entry_id,
            "pdf_url": result.pdf_url,
            "primary_category": result.primary_category,
            "categories": result.categories,
            "published": result.published.isoformat(),
            "updated": result.updated.isoformat(),
            "doi": result.doi,
            "comment": result.comment,
            "journal_ref": result.journal_ref,
        }

    return {"error": f"Paper not found: {ids[0]}"}
