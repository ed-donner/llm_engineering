"""
answer.py — RAG answer pipeline for research papers/books.

Uses:
- ChromaDB collection created by ingest.py
- OpenAI embeddings for retrieval
- LiteLLM for answering/reranking
- metadata-aware context formatting

Entry points:
    answer_question("What is scaled dot-product attention?")
    quick_test("What BLEU score did Transformer achieve?")
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple

import chromadb
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from tenacity import retry, wait_exponential
from litellm import completion
from openai import OpenAI
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from rank_bm25 import BM25Okapi
import re



load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# CONFIG
# ------------------------------------------------------------------ #
#"groq/openai/gpt-oss-120b"
ANSWER_MODEL = "gemini/gemini-2.5-flash-lite"
RERANK_MODEL = "gemini/gemini-2.5-flash-lite"
REWRITE_MODEL = "groq/openai/gpt-oss-20b"

EMBEDDING_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "research_brain"

CHROMA_TENANT = os.getenv("CHROMA_TENANT", "")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE", "")
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY", "")

RETRIEVAL_K = 8
FINAL_K = 5

wait = wait_exponential(multiplier=1, min=10, max=240)



# ------------------------------------------------------------------ #
# MODELS
# ------------------------------------------------------------------ #

class RetrievedChunk(BaseModel):
    page_content: str
    metadata: dict
    score: float | None = None


class RankOrder(BaseModel):
    order: List[int] = Field(
        description="Chunk ids ordered from most relevant to least relevant."
    )


# ------------------------------------------------------------------ #
# VECTOR STORE
# ------------------------------------------------------------------ #

def get_embedding_model():
    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def get_vector_store(use_cloud: bool = True) -> Chroma:
    embeddings = get_embedding_model()

    if use_cloud and CHROMA_TENANT and CHROMA_API_KEY:
        logger.info("Connecting to ChromaDB Cloud")
        client = chromadb.CloudClient(
            tenant=CHROMA_TENANT,
            database=CHROMA_DATABASE,
            api_key=CHROMA_API_KEY,
        )

        return Chroma(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
        )

    logger.info("Using local ChromaDB")
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory="./chroma_db",
    )


# ------------------------------------------------------------------ #
# QUERY REWRITING
# ------------------------------------------------------------------ #

@retry(wait=wait)
def rewrite_query(question: str, history: List[dict] | None = None) -> str:
    history = history or []

    prompt = f"""
You are helping search a research knowledge base containing academic papers, books, tables, equations, and figure captions.

Rewrite the user's question into a short retrieval query that is likely to surface the most relevant chunks.

Conversation history:
{history}

User question:
{question}

Rules:
- Return only the rewritten search query.
- Keep it short.
- Preserve technical terms.
- Do not answer the question.
"""
    response = completion(
        messages=[
            {
                "role": "user",
                "content": prompt}
                ], model = "groq/openai/gpt-oss-20b"
                )
    

    return response.choices[0].message.content.strip()


# ------------------------------------------------------------------ #
# RETRIEVAL
# ------------------------------------------------------------------ #


def fetch_context_unranked(
    vector_store: Chroma,
    question: str,
    k: int = RETRIEVAL_K,
    include_references: bool = False,
) -> List[RetrievedChunk]:

    where = None
    if not include_references:
        where = {
            "section_title": {
                "$nin": [
                    "References",
                    "Preamble",
                    "Acknowledgements",
                    "Acknowledgments",
                    "Appendix",
                ]
            }
        }
    results = vector_store.similarity_search_with_score(
        question,
        k=k,
        filter=where,)

    chunks = []

    for doc, score in results:
        chunks.append(
            RetrievedChunk(
                page_content=doc.page_content,
                metadata=doc.metadata,
                score=score,
            )
        )
    return chunks


def merge_chunks(
    chunks_a: List[RetrievedChunk],
    chunks_b: List[RetrievedChunk],
    k: int = 60,
) -> List[RetrievedChunk]:
    """Reciprocal Rank Fusion merge."""
    scores = {}
    chunk_map = {}

    for rank, chunk in enumerate(chunks_a):
        key = (
            chunk.metadata.get("document_id", ""),
            chunk.metadata.get("chunk_index", ""),
        )
        scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
        chunk_map[key] = chunk

    for rank, chunk in enumerate(chunks_b):
        key = (
            chunk.metadata.get("document_id", ""),
            chunk.metadata.get("chunk_index", ""),
        )
        scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
        if key not in chunk_map:
            chunk_map[key] = chunk

    # Sort by fused score descending
    ranked_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)

    return [chunk_map[key] for key in ranked_keys]


  


# ------------------------------------------------------------------ #
# RERANKING
# ------------------------------------------------------------------ #

@retry(wait=wait)
def rerank(question: str, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
    if not chunks:
        return []

    system_prompt = """
You are a research document re-ranker.

You are given:
- a user question
- retrieved chunks from academic papers/books

Rank chunks by relevance to the question.

Rules:
- Return all chunk ids, comma separated.
- put a comma after every chunk id.
- Most relevant first.
- Prefer chunks that directly answer the question.
- Prefer chunks with equations, tables, section titles, or figure captions if relevant.
- Return valid JSON only in this exact format:
{"order":[4,6,1,2,3]}
- The order array must contain separate integers with commas.
- Do not concatenate numbers.
- Do not return chunk ids larger than the number of chunks provided.
"""

    user_prompt = f"Question:\n{question}\n\nChunks:\n\n"

    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.metadata

        source = Path(meta.get("source", "")).name
        section = meta.get("section_title", "")
        topic = meta.get("topic", "")
        summary = meta.get("summary", "")
        pages = f"{meta.get('page_start', '?')}-{meta.get('page_end', '?')}"

        user_prompt += (
            f"# CHUNK ID: {i}\n"
            f"Source: {source}\n"
            f"Section: {section}\n"
            f"Topic: {topic}\n"
            f"Summary: {summary}\n"
            f"Pages: {pages}\n"
            f"Text:\n{chunk.page_content[:1200]}\n\n"
        )

    response = completion(
        model="gemini/gemini-2.5-flash-lite",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    reply = response.choices[0].message.content
    order = RankOrder.model_validate_json(reply).order
    
    reranked = []

    for i in order:
        if 1 <= i <= len(chunks):
            reranked.append(chunks[i - 1])

    return reranked

# Build BM25 index from chunks (call once after loading vector store)
def build_bm25_index(vector_store):
    results = vector_store.get(include=["documents", "metadatas"])
    
    documents = results["documents"]
    metadatas = results["metadatas"]
    ids = results["ids"]
    
    # Combine content + metadata for BM25 indexing
    enriched_docs = []
    for doc, meta in zip(documents, metadatas):
        extra = " ".join([
            meta.get("section_title", ""),
            meta.get("topic", ""),
            meta.get("equation_description", ""),
        ])
        enriched_docs.append(f"{doc} {extra}")
    
    tokenized = [
        re.findall(r"\w+", doc.lower())
        for doc in enriched_docs
    ]
    
    bm25 = BM25Okapi(tokenized)
    
    # Return original documents for retrieval, not enriched
    return bm25, documents, metadatas, ids


def bm25_search(
    bm25, documents, metadatas, ids,
    question: str, k: int = 10,
) -> List[RetrievedChunk]:
    """Keyword search using BM25."""
    tokenized_query = re.findall(r"\w+", question.lower())
    scores = bm25.get_scores(tokenized_query)
    
    top_indices = sorted(
        range(len(scores)), 
        key=lambda i: scores[i], 
        reverse=True,
    )[:k]
    
    chunks = []
    for i in top_indices:
        if scores[i] > 0:
            chunks.append(RetrievedChunk(
                page_content=documents[i],
                metadata=metadatas[i],
                score=float(scores[i]),
            ))
    
    return chunks

def fetch_context(
    vector_store: Chroma,
    question: str,
    history: List[dict] | None = None,
    bm25_index=None,
) -> List[RetrievedChunk]:
    history = history or []

    rewritten = rewrite_query(question, history)

    query_text = f"{question} {rewritten}".lower()
    include_references = "reference" in query_text or "citation" in query_text

    chunks_original = fetch_context_unranked(vector_store, question, include_references = include_references)
    chunks_rewritten = fetch_context_unranked(vector_store, rewritten, include_references = include_references)

    # BM25 on both original and rewritten
    bm25_chunks = []
    if bm25_index:
        bm25, documents, metadatas, ids = bm25_index
        bm25_chunks = bm25_search(bm25, documents, metadatas, ids, question, k=10)

    merged = merge_chunks(chunks_original, chunks_rewritten)
    merged = merge_chunks(merged, bm25_chunks)

    reranked = rerank(question, merged)

    return reranked[:FINAL_K]





def fetch_context_fast(vector_store, question: str, k: int = 5, bm25_index=None):
    """Hybrid retrieval: vector + BM25, merged and deduplicated."""
    include_references = "reference" in question.lower()
    # Vector search
    vector_chunks = fetch_context_unranked(
        vector_store=vector_store,
        question=question,
        k=10,
        include_references=include_references,
     
    )
    
    bm25_chunks = []
    if bm25_index:
        bm25, documents, metadatas, ids = bm25_index
        bm25_chunks = bm25_search(bm25, documents, metadatas, ids, question, k=10)
    
    return merge_chunks(vector_chunks, bm25_chunks)[:k]


# ------------------------------------------------------------------ #
# ANSWERING
# ------------------------------------------------------------------ #

SYSTEM_PROMPT = """
You are a careful research assistant.

You answer questions using retrieved context from academic papers, books, tables, equations, and figure captions.

Rules:
- Answer ONLY from the provided context.
- If the retrieved context partially answers the question, provide the partial answer instead of saying you don't know.
- If a figure or table is mentioned in the retrieved context, use the caption and surrounding explanatory text to answer even if the full visual content is unavailable.
- Only say "I don't know" if the retrieved context contains no relevant information at all.
- Be accurate and concise.
- For technical questions, explain clearly.
- For equations, preserve mathematical meaning.
- For comparisons, explicitly compare the relevant sources or sections.
- Mention source titles/sections/pages when useful.
- Do not hallucinate.
- Do not cite sources that are not in the context.

Context:
{context}
"""


def format_context(chunks: List[RetrievedChunk]) -> str:
    blocks = []

    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.metadata

        source = Path(meta.get("source", "")).name
        title = meta.get("title", "")
        section = meta.get("section_title", "")
        topic = meta.get("topic", "")
        summary = meta.get("summary", "")
        pages = f"{meta.get('page_start', '?')}-{meta.get('page_end', '?')}"
        block = f"""
[Source {i}]
File: {source}
Title: {title}

Section: {section}
Topic: {topic}
Summary: {summary}
Pages: {pages}

Text:
{chunk.page_content}
"""

        blocks.append(block.strip())

    return "\n\n---\n\n".join(blocks)


def make_rag_messages(
    question: str,
    history: List[dict],
    chunks: List[RetrievedChunk],
) -> List[dict]:
    context = format_context(chunks)

    system_prompt = SYSTEM_PROMPT.format(context=context)

    return (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": question}]
    )


@retry(wait=wait)
def answer_question(
    question: str,
    history: List[dict] | None = None,
    vector_store: Chroma | None = None,
    use_cloud: bool = True,
    mode: str = "fast",
    k: int = 5,
    bm25_index=None,

) -> Tuple[str, List[RetrievedChunk]]:
    """
    mode="fast"
        - direct retrieval only
        - lower latency
        - ideal for voice/chat

    mode="accurate"
        - query rewrite + rerank
        - slower but higher quality
    """
    history = history or []

    if vector_store is None:
        vector_store = get_vector_store(use_cloud=use_cloud)

    # Fast mode
    if mode == "fast":
        chunks = fetch_context_fast(
            vector_store=vector_store,
            question=question,
            k=k,
            bm25_index=bm25_index,
         
        )

    # Accurate mode
    else:
        chunks = fetch_context(
            vector_store=vector_store,
            question=question,
            history=history,
            bm25_index=bm25_index,
          
        )
    messages = make_rag_messages(question, history, chunks)

    response = completion(
        model=ANSWER_MODEL,
        messages=messages,
    )

    answer = response.choices[0].message.content

    return answer, chunks






def stream_answer_with_sources(
    question: str,
    history: List[dict] | None = None,
    vector_store: Chroma | None = None,
    use_cloud: bool = True,
    mode: str = "fast",
    k: int = 5,
    bm25_index=None
):
    """
    Streams answer and also returns chunks after completion.

    Useful for notebooks/FastAPI later.
    """
    history = history or []

    if vector_store is None:
        vector_store = get_vector_store(use_cloud=use_cloud)

    if mode == "fast":
        chunks = fetch_context_fast(vector_store, question, k=k, bm25_index=bm25_index,)
    else:
        chunks = fetch_context(vector_store, question, history, bm25_index=bm25_index,)

    messages = make_rag_messages(question, history, chunks)

    response = completion(
        model=ANSWER_MODEL,
        messages=messages,
        stream=True,
    )

    full_answer = ""

    for event in response:
        delta = event["choices"][0]["delta"].get("content", "")
        if delta:
            full_answer += delta
           

    

    return full_answer, chunks




    