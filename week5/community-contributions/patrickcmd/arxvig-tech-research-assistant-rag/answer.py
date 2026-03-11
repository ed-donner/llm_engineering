from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv
from chromadb import PersistentClient
from litellm import completion
from pydantic import BaseModel, Field
from tenacity import retry, wait_exponential


load_dotenv(override=True)

MODEL = "openai/gpt-4.1-mini"
DB_NAME = str(Path(__file__).parent / "arxiv_db")
COLLECTION_NAME = "arxiv_papers"
EMBEDDING_MODEL = "text-embedding-3-large"
WAIT = wait_exponential(multiplier=1, min=10, max=240)

RETRIEVAL_K = 20
FINAL_K = 10

openai = OpenAI()
chroma = PersistentClient(path=DB_NAME)
collection = chroma.get_or_create_collection(COLLECTION_NAME)

SYSTEM_PROMPT = """You are a knowledgeable research assistant that answers questions about academic papers from arXiv.
Your answers should be accurate, technically precise, and grounded in the provided paper excerpts.
If the context doesn't contain enough information to answer, say so.

Here are relevant excerpts from arXiv papers:

{context}

Answer the user's question based on these excerpts. Cite paper titles when referencing specific findings."""


class Result(BaseModel):
    page_content: str
    metadata: dict


class RankOrder(BaseModel):
    order: list[int] = Field(
        description="Chunk ids ordered from most relevant to least relevant"
    )


@retry(wait=WAIT)
def rerank(question: str, chunks: list[Result]) -> list[Result]:
    """Re-rank retrieved chunks by relevance to the question using an LLM."""
    system_prompt = (
        "You are a document re-ranker for academic paper excerpts. "
        "Given a question and numbered chunks, rank all chunks by relevance. "
        "Reply only with the ranked list of chunk ids."
    )
    user_prompt = f"Question:\n{question}\n\nRank all chunks by relevance.\n\n"
    for idx, chunk in enumerate(chunks):
        user_prompt += f"# CHUNK ID: {idx + 1}:\n\n{chunk.page_content}\n\n"
    user_prompt += "Reply only with the list of ranked chunk ids."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = completion(model=MODEL, messages=messages, response_format=RankOrder)
    reply = response.choices[0].message.content
    order = RankOrder.model_validate_json(reply).order
    return [chunks[i - 1] for i in order if 1 <= i <= len(chunks)]


@retry(wait=WAIT)
def rewrite_query(question: str, history: list[dict] | None = None) -> str:
    """Rewrite the user's question into a concise query optimised for retrieval."""
    history = history or []
    message = f"""You are helping a user find information in a knowledge base of arXiv research papers.

Conversation history:
{history}

Current question:
{question}

Respond ONLY with a short, refined search query most likely to surface relevant paper content."""

    response = completion(model=MODEL, messages=[{"role": "system", "content": message}])
    return response.choices[0].message.content


def fetch_context_unranked(question: str) -> list[Result]:
    """Embed the question and retrieve the top-K chunks from ChromaDB."""
    query_vec = openai.embeddings.create(model=EMBEDDING_MODEL, input=[question]).data[0].embedding
    results = collection.query(query_embeddings=[query_vec], n_results=RETRIEVAL_K)

    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append(Result(page_content=doc, metadata=meta))
    return chunks


def merge_chunks(chunks: list[Result], reranked: list[Result]) -> list[Result]:
    """Merge two chunk lists, deduplicating by page_content."""
    merged = chunks[:]
    existing = {c.page_content for c in chunks}
    for chunk in reranked:
        if chunk.page_content not in existing:
            merged.append(chunk)
            existing.add(chunk.page_content)
    return merged


def fetch_context(question: str) -> list[Result]:
    """Retrieve context using both the original and a rewritten query, then re-rank."""
    rewritten = rewrite_query(question)
    chunks_original = fetch_context_unranked(question)
    chunks_rewritten = fetch_context_unranked(rewritten)
    merged = merge_chunks(chunks_original, chunks_rewritten)
    reranked = rerank(question, merged)
    return reranked[:FINAL_K]


def make_rag_messages(
    question: str, history: list[dict], chunks: list[Result]
) -> list[dict]:
    """Build the full message list for the final answer LLM call."""
    context = "\n\n".join(
        f"[{chunk.metadata.get('title', 'Unknown')}] "
        f"({chunk.metadata.get('arxiv_url', '')}):\n{chunk.page_content}"
        for chunk in chunks
    )
    system = SYSTEM_PROMPT.format(context=context)
    return [{"role": "system", "content": system}] + history + [{"role": "user", "content": question}]


@retry(wait=WAIT)
def answer_question(question: str, history: list[dict] | None = None) -> tuple[str, list[Result]]:
    """Answer a question using RAG over the ingested arXiv papers."""
    history = history or []
    chunks = fetch_context(question)
    messages = make_rag_messages(question, history, chunks)
    response = completion(model=MODEL, messages=messages)
    return response.choices[0].message.content, chunks