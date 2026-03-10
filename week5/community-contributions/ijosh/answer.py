"""
Advanced RAG answer pipeline for Insurellm knowledge base.

Key improvements over baseline:
- Dual retrieval: query with both the original question and an LLM-rewritten version,
  then merge results to maximise recall.
- LLM reranking: reorder the merged candidate pool so the most relevant chunks come first.
- OpenAI text-embedding-3-large: higher-dimensional, more accurate embeddings.
- Prompt tuned for accuracy + completeness + relevance (the three eval axes).
"""

from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from chromadb import PersistentClient
from litellm import completion
from pydantic import BaseModel, Field
from tenacity import retry, wait_exponential


load_dotenv(override=True)

MODEL = "openai/gpt-4.1-nano"
DB_NAME = str(Path(__file__).parent.parent / "week5_solution_db")
COLLECTION_NAME = "docs"
EMBEDDING_MODEL = "text-embedding-3-large"

wait = wait_exponential(multiplier=1, min=10, max=240)

# Retrieve a large candidate pool then trim after reranking
RETRIEVAL_K = 20
FINAL_K = 10

openai = OpenAI()
chroma = PersistentClient(path=DB_NAME)
collection = chroma.get_or_create_collection(COLLECTION_NAME)


# ---------------------------------------------------------------------------
# System prompt — tuned for the three evaluation dimensions
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a precise, knowledgeable assistant for Insurellm, an insurance technology company.

Your answers are evaluated on three strict criteria:
• ACCURACY   – every fact, number, name, date, salary, price, and identifier must be exactly right.
• COMPLETENESS – include ALL relevant details from the context that answer the question; omit nothing important.
• RELEVANCE  – answer only what was asked; do not add unrequested information or padding.

Rules:
- Quote specific values (numbers, prices, percentages, dates) exactly as they appear in the context.
- If the question has multiple parts, address every part.
- If the answer is not in the context, say you don't know rather than guessing.

Context extracted from the Insurellm Knowledge Base:
{context}

Using the context above, answer the user's question with full accuracy, completeness, and relevance."""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
class Result(BaseModel):
    page_content: str
    metadata: dict


class RankOrder(BaseModel):
    order: list[int] = Field(
        description="Chunk IDs (1-based) ordered from most relevant to least relevant"
    )


# ---------------------------------------------------------------------------
# Query rewriting
# ---------------------------------------------------------------------------
@retry(wait=wait)
def rewrite_query(question: str, history: list[dict] = []) -> str:
    """Rewrite the user question into a compact, entity-focused KB search query."""
    prompt = f"""You are preparing a search query for a corporate knowledge base about Insurellm.

Conversation so far: {history}
User question: {question}

Rewrite this as a short, precise search query that will surface the most relevant facts.
Include key entity names, product names, person names, contract numbers, and specific terms.
Output ONLY the search query — no explanation, no punctuation wrapper."""
    response = completion(model=MODEL, messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Retrieval helpers
# ---------------------------------------------------------------------------
def _embed(text: str) -> list[float]:
    return openai.embeddings.create(model=EMBEDDING_MODEL, input=[text]).data[0].embedding


def _retrieve(query: str, k: int = RETRIEVAL_K) -> list[Result]:
    vector = _embed(query)
    results = collection.query(query_embeddings=[vector], n_results=k)
    return [
        Result(page_content=doc, metadata=meta)
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]


def _merge_unique(a: list[Result], b: list[Result]) -> list[Result]:
    seen: set[str] = set()
    merged: list[Result] = []
    for chunk in a + b:
        if chunk.page_content not in seen:
            seen.add(chunk.page_content)
            merged.append(chunk)
    return merged


# ---------------------------------------------------------------------------
# LLM reranking
# ---------------------------------------------------------------------------
@retry(wait=wait)
def rerank(question: str, chunks: list[Result]) -> list[Result]:
    """Ask the LLM to reorder chunks from most to least relevant."""
    if not chunks:
        return chunks

    system_prompt = (
        "You are a relevance ranker. Given a question and a numbered list of document chunks, "
        "return their IDs ordered from most to least relevant to answering the question. "
        "Consider which chunks contain the specific facts, names, and values needed."
    )
    user_prompt = f"Question: {question}\n\nChunks:\n\n"
    for i, chunk in enumerate(chunks, 1):
        # Truncate for prompt efficiency — headline + summary is enough to rank
        preview = chunk.page_content[:600]
        user_prompt += f"CHUNK {i}:\n{preview}\n\n"
    user_prompt += "Return the ordered chunk IDs."

    response = completion(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=RankOrder,
    )
    order = RankOrder.model_validate_json(response.choices[0].message.content).order

    # Safely map back; append anything the LLM omitted at the end
    seen: set[int] = set()
    reranked: list[Result] = []
    for idx in order:
        if 1 <= idx <= len(chunks) and idx not in seen:
            reranked.append(chunks[idx - 1])
            seen.add(idx)
    for i in range(1, len(chunks) + 1):
        if i not in seen:
            reranked.append(chunks[i - 1])
    return reranked


# ---------------------------------------------------------------------------
# Public API expected by the evaluator
# ---------------------------------------------------------------------------
def fetch_context(question: str) -> list[Result]:
    """
    Dual retrieval (original + rewritten query) → merge → LLM rerank → top FINAL_K.
    This is also called directly by the retrieval evaluator.
    """
    rewritten = rewrite_query(question)
    pool = _merge_unique(_retrieve(question), _retrieve(rewritten))
    ranked = rerank(question, pool)
    return ranked[:FINAL_K]


def make_rag_messages(question: str, history: list[dict], chunks: list[Result]) -> list[dict]:
    context = "\n\n---\n\n".join(
        f"[Source: {c.metadata.get('source', 'unknown')}]\n{c.page_content}"
        for c in chunks
    )
    system = SYSTEM_PROMPT.format(context=context)
    return [{"role": "system", "content": system}] + history + [{"role": "user", "content": question}]


@retry(wait=wait)
def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Result]]:
    """
    Full RAG pipeline: dual retrieval → rerank → generate answer.
    Returns (answer_text, retrieved_chunks).
    """
    chunks = fetch_context(question)
    messages = make_rag_messages(question, history, chunks)
    response = completion(model=MODEL, messages=messages)
    return response.choices[0].message.content, chunks
